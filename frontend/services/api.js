import axios from 'axios';

const API_BASE = '/api';

export const videoApi = {
  upload: (formData, onProgress) => axios.post(`${API_BASE}/video/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  }),
  getStatus: (videoId) => axios.get(`${API_BASE}/video/status/${videoId}`),
  getResult: (videoId) => `${API_BASE}/video/result/${videoId}`,
  listResults: () => axios.get(`${API_BASE}/video/results`),
  deleteResult: (videoId) => axios.delete(`${API_BASE}/video/result/${videoId}`),
};

export const imageApi = {
  process: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return axios.post(`${API_BASE}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const varroaApi = {
  process: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return axios.post(`${API_BASE}/varroa`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

