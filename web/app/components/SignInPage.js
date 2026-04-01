"use client";
import { SignInButton } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <main className="flex-1 min-h-screen flex items-center justify-center bg-[#0a0a14] w-full">
      <div className="text-center p-12 glass-panel max-w-md w-full border border-white/5 rounded-3xl bg-white/[0.02]">
        <div className="w-20 h-20 bg-[#7c5cfc1a] rounded-full flex items-center justify-center mx-auto mb-6">
          <span className="text-4xl text-[#7c5cfc]">◆</span>
        </div>
        <h1 className="text-3xl font-bold mb-4 gradient-text">Pivot.AI</h1>
        <p className="text-[#8a8ca0] mb-8 leading-relaxed">
          Welcome to the future of AI-native career design. Securely sign in to access your dashboard.
        </p>
        <div className="flex flex-col gap-4">
          <SignInButton mode="modal">
            <button className="px-8 py-3 bg-[#7c5cfc] hover:bg-[#6a4ce0] text-white font-bold rounded-xl transition-all shadow-lg shadow-[#7c5cfc]/20 w-full">
              Sign In
            </button>
          </SignInButton>
        </div>
      </div>
    </main>
  );
}
