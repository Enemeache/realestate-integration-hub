import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PropLeads Dashboard",
  description: "Panel de leads consumiendo la API GraphQL de PropLeads Integration Hub",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
