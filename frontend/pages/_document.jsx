import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta name="theme-color" content="#FAF6EC" />
        <meta
          name="description"
          content="Buzzlytics — computer-vision colony-health monitoring for beekeepers. Watch your hive, catch trouble early."
        />
      </Head>
      <body className="bg-paper text-ink antialiased">
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
