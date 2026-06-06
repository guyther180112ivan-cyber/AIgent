import { Construction } from 'lucide-react';

export default function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-16 sm:py-24 text-center px-4">
      <div className="w-14 h-14 sm:w-16 sm:h-16 bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
        <Construction className="w-7 h-7 sm:w-8 sm:h-8 text-gray-500" />
      </div>
      <h2 className="text-lg sm:text-xl font-bold text-white mb-2">{title}</h2>
      <p className="text-gray-500 text-sm">Раздел в разработке</p>
    </div>
  );
}
