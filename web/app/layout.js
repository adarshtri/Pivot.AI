import { ClerkProvider } from "@clerk/nextjs";
import { auth } from "@clerk/nextjs/server";
import NavContent from "./components/NavContent";
import SignInPage from "./components/SignInPage";
import "./globals.css";

export const metadata = {
  title: "Pivot.AI — Command Center",
  description: "Accelerate your career with AI.",
};

export default async function RootLayout({ children }) {
  const { userId } = await auth();
  const isAuthenticated = !!userId;

  return (
    <ClerkProvider>
      <html lang="en">
        <head>
          <link
            href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
            rel="stylesheet"
          />
        </head>
        <body className="flex min-h-screen">
          {isAuthenticated ? (
            <>
              <NavContent />
              <main className="ml-[240px] flex-1 min-h-screen">
                <div className="max-w-[1200px] mx-auto px-8 py-10">
                  {children}
                </div>
              </main>
            </>
          ) : (
            <SignInPage />
          )}
        </body>
      </html>
    </ClerkProvider>
  );
}


