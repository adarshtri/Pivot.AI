"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton, useUser } from "@clerk/nextjs";

const navItems = [
  { href: "/", label: "Dashboard", icon: "◆" },
  { href: "/profile", label: "Profile", icon: "👤" },
  { href: "/goals", label: "Goals", icon: "🎯" },
  { href: "/companies", label: "Companies", icon: "🏢" },
  { href: "/jobs", label: "Jobs", icon: "📋" },
  { href: "/strategist", label: "Strategist", icon: "🧠" },
  { href: "/learning-hub", label: "Learning Hub", icon: "🎓" },
  { href: "/resume", label: "Resume", icon: "📄" },
];

export default function NavContent() {
  const pathname = usePathname();
  const { user } = useUser();
  const isAdmin = user?.publicMetadata?.isAdmin || user?.emailAddresses[0]?.emailAddress === "admin@pivot.ai";

  return (
    <nav className="fixed top-0 left-0 bottom-0 w-[240px] flex flex-col py-6"
      style={{ background: "var(--bg-surface)", borderRight: "1px solid rgba(255,255,255,0.06)" }}>
      
      <div className="px-6 mb-10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl gradient-text font-bold">◆</span>
          <span className="text-lg font-bold tracking-tight">Pivot.AI</span>
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-1 px-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all relative no-underline
                ${isActive
                  ? "text-white"
                  : "text-[#8a8ca0] hover:text-white hover:bg-white/[0.04]"
                }`}
              style={isActive ? { background: "rgba(124, 92, 252, 0.15)" } : {}}
            >
              {isActive && (
                <span className="absolute left-[-12px] top-[6px] bottom-[6px] w-[3px] rounded-sm"
                  style={{ background: "linear-gradient(135deg, #7c5cfc, #5b8def)" }} />
              )}
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
        
        {/* Show Admin link for admin users */}
        {isAdmin && (
          <Link
            href="/admin"
            className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all relative mt-auto mb-2 no-underline
              ${pathname === "/admin"
                ? "text-white"
                : "text-[#8a8ca0] hover:text-white hover:bg-white/[0.04]"
              }`}
            style={pathname === "/admin" ? { background: "rgba(124, 92, 252, 0.15)" } : {}}
          >
            {pathname === "/admin" && (
              <span className="absolute left-[-12px] top-[6px] bottom-[6px] w-[3px] rounded-sm"
                style={{ background: "linear-gradient(135deg, #7c5cfc, #5b8def)" }} />
            )}
            <span className="text-base">⚙️</span>
            <span>Admin</span>
          </Link>
        )}
      </div>

      <div className="px-6 pt-4 flex items-center justify-between" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        <span className="text-xs text-[#5a5c72]">v0.1.0</span>
        <UserButton afterSignOutUrl="/" />
      </div>
    </nav>
  );
}
