import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CAPTCHA Solving & Verification Tool",
  description:
    "Recognize, solve, and verify CAPTCHAs in an authorized test environment.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="app">
          <h1>CAPTCHA Solving &amp; Verification Tool</h1>
          <p>
            Authorized test environment — synthetic CAPTCHAs &amp; official
            provider test keys only.
          </p>
        </header>
        <main className="wrap">{children}</main>
      </body>
    </html>
  );
}
