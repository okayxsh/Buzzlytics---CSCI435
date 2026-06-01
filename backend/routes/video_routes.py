"""Video upload and processing routes for Buzzlytics API.

Provides endpoints for uploading video files, processing them through the
computer vision pipeline, retrieving annotated results, listing processed
videos, and deleting video records.
"""

import sys
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

# Add the parent directory to sys.path so cv_pipeline can be imported
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cv_pipeline import CVPipeline

router = APIRouter(prefix="/api/video", tags=["video"])

# Directory paths
UPLOADS_DIR = BACKEND_DIR / "uploads"
RESULTS_DIR = BACKEND_DIR / "results"

# In-memory storage for processing status and video metadata
# Key: video_id, Value: dict with status, paths, summary, etc.
_processing_store: Dict[str, Dict[str, Any]] = {}


def _process_video_task(video_id: str, input_path: str, output_path: str) -> None:
    """Background task that processes an uploaded video through the CV pipeline.

    Args:
        video_id: Unique identifier for this video processing job.
        input_path: Path to the uploaded original video file.
        output_path: Path where the annotated video will be saved.
    """
    try:
        _processing_store[video_id]["status"] = "processing"
        print(f"[VideoRoutes] Processing video {video_id}...")

        pipeline = CVPipeline()
        # process_video is a generator that yields progress and returns final result
        gen = pipeline.process_video(input_path, output_path)
        result = None
        while True:
            try:
                progress_info = next(gen)
                _processing_store[video_id]["progress"] = progress_info.get("progress", 0.0)
            except StopIteration as e:
                # The generator's return value is stored in StopIteration.value
                result = e.value
                break

        # Extract summary data from the pipeline result
        summary: Dict[str, Any] = {}
        if isinstance(result, dict):
            total_frames = result.get("total_frames", 0)
            avg_bees = result.get("avg_bees", 0.0)
            final_summary = result.get("final_summary", {})
            summary = {
                "total_frames": total_frames,
                "avg_bees": avg_bees,
                "final_summary": final_summary,
            }
        else:
            # If process_video returns something unexpected, store it raw
            summary = {"raw_result": str(result)}

        _processing_store[video_id]["status"] = "completed"
        _processing_store[video_id]["summary"] = summary
        _processing_store[video_id]["annotated_path"] = str(output_path)
        print(f"[VideoRoutes] Video {video_id} processing completed.")

    except Exception as exc:
        _processing_store[video_id]["status"] = "failed"
        _processing_store[video_id]["error"] = str(exc)
        print(f"[VideoRoutes] Video {video_id} processing failed: {exc}")


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """Upload a video file for processing.

    Accepts a multipart video file upload, saves it to the uploads directory,
    and starts background processing through the CV pipeline. Returns a
    video_id and task_id immediately so the client can poll for status.

    Args:
        background_tasks: FastAPI background tasks runner.
        file: The uploaded video file.

    Returns:
        JSON dict with video_id, original_path, status, and task_id.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Generate a unique video ID
    video_id = str(uuid.uuid4())

    # Ensure upload directories exist
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Determine file extension and build paths
    file_ext = Path(file.filename).suffix or ".mp4"
    original_path = UPLOADS_DIR / f"{video_id}{file_ext}"
    annotated_path = RESULTS_DIR / f"{video_id}_annotated{file_ext}"

    # Save the uploaded file
    try:
        contents = await file.read()
        with open(original_path, "wb") as f:
            f.write(contents)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {exc}",
        )

    # Store initial metadata
    _processing_store[video_id] = {
        "video_id": video_id,
        "original_path": str(original_path),
        "annotated_path": None,
        "original_filename": file.filename,
        "summary": None,
        "status": "queued",
        "error": None,
    }

    # Enqueue background processing
    task_id = str(uuid.uuid4())
    background_tasks.add_task(
        _process_video_task,
        video_id,
        str(original_path),
        str(annotated_path),
    )

    return {
        "video_id": video_id,
        "original_path": str(original_path),
        "status": "queued",
        "task_id": task_id,
    }


@router.get("/status/{video_id}")
async def get_processing_status(video_id: str) -> Dict[str, Any]:
    """Check the processing status of a video.

    Args:
        video_id: The unique identifier of the video.

    Returns:
        JSON dict with the current processing status and any error details.
    """
    if video_id not in _processing_store:
        raise HTTPException(status_code=404, detail="Video ID not found")

    record = _processing_store[video_id]
    response: Dict[str, Any] = {
        "video_id": video_id,
        "status": record["status"],
    }

    if record["status"] == "completed" and record.get("summary"):
        # Frontend expects 'result' key with the summary data
        response["result"] = record["summary"]

    if record.get("progress") is not None:
        response["progress"] = record["progress"]

    if record["status"] == "failed" and record.get("error"):
        response["error"] = record["error"]

    return response


@router.get("/result/{video_id}")
async def get_annotated_video(video_id: str):
    """Stream the annotated video file for a processed video.

    Args:
        video_id: The unique identifier of the video.

    Returns:
        StreamingResponse with the annotated video file.
    """
    if video_id not in _processing_store:
        raise HTTPException(status_code=404, detail="Video ID not found")

    record = _processing_store[video_id]

    if record["status"] != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Video processing not completed. Current status: {record['status']}",
        )

    annotated_path = record.get("annotated_path")
    if not annotated_path or not Path(annotated_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Annotated video file not found on disk",
        )

    file_path = Path(annotated_path)
    file_size = file_path.stat().st_size

    def _iter_file():
        """Generator that yields file chunks for streaming."""
        with open(file_path, "rb") as f:
            while chunk := f.read(64 * 1024):  # 64 KB chunks
                yield chunk

    return StreamingResponse(
        _iter_file(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"inline; filename={video_id}_annotated.mp4",
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
        },
    )


@router.get("/results")
async def list_processed_videos() -> Dict[str, Any]:
    """List all processed videos and their statuses.

    Returns:
        JSON dict with a list of video records including video_id,
        original_filename, status, and summary (if available).
    """
    videos = []
    for video_id, record in _processing_store.items():
        entry: Dict[str, Any] = {
            "video_id": video_id,
            "original_filename": record.get("original_filename", "unknown"),
            "status": record["status"],
        }
        if record.get("summary"):
            entry["summary"] = record["summary"]
        if record.get("error"):
            entry["error"] = record["error"]
        videos.append(entry)

    return {"videos": videos, "total": len(videos)}


@router.delete("/result/{video_id}")
async def delete_processed_video(video_id: str) -> Dict[str, Any]:
    """Delete a processed video and its associated files.

    Removes the original uploaded video, the annotated result video,
    and the processing record from memory.

    Args:
        video_id: The unique identifier of the video to delete.

    Returns:
        JSON dict confirming deletion.
    """
    if video_id not in _processing_store:
        raise HTTPException(status_code=404, detail="Video ID not found")

    record = _processing_store[video_id]

    # Remove original file from disk
    original_path = record.get("original_path")
    if original_path and Path(original_path).exists():
        try:
            Path(original_path).unlink()
        except OSError as exc:
            print(f"[VideoRoutes] Failed to delete original file {original_path}: {exc}")

    # Remove annotated file from disk
    annotated_path = record.get("annotated_path")
    if annotated_path and Path(annotated_path).exists():
        try:
            Path(annotated_path).unlink()
        except OSError as exc:
            print(f"[VideoRoutes] Failed to delete annotated file {annotated_path}: {exc}")

    # Remove from in-memory store
    del _processing_store[video_id]

    return {"message": f"Video {video_id} deleted successfully", "video_id": video_id}
