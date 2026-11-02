import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SHARKMMO — Admin Dashboard",
  description: "Hệ sinh thái sản phẩm MMO tự động — Quản trị viên",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="dark">
      <body className="bg-shark-bg text-shark-text antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
