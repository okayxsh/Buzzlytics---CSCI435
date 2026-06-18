import '../styles/globals.css';
import { Fraunces, Raleway } from 'next/font/google';

const display = Fraunces({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '900'],
  style: ['normal', 'italic'],
  variable: '--font-display',
  display: 'swap',
});

const body = Raleway({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-body',
  display: 'swap',
});

export default function App({ Component, pageProps }) {
  return (
    <div className={`${display.variable} ${body.variable} font-body`}>
      <Component {...pageProps} />
    </div>
  );
}
