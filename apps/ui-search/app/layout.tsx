import './globals.css';

export const metadata = {
  title: 'Editorial Knowledge Search',
  description: 'Search through curated knowledge from trusted sources',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}