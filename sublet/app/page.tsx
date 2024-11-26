import Image from "next/image";

export default function Home() {
  return (
    <main className="space-y-10">
      <h1 className="mt-40 text-5xl font-bold text-center tracking-tight text-white">
        <span className="bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
          Welcome to Sublet@Portal
        </span>
      </h1>
      <div className="space-y-5">
        <div className="flex justify-center">
          <Image src="/penn-mobile.svg" alt="Sublet@Portal Logo" width={200} height={200} />
        </div>
        <p className="text-center">The best place to sublet your room to other students!</p>
      </div>
    </main>
  );
}
