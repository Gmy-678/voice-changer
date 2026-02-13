import React from 'react';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
}

export const Toggle: React.FC<ToggleProps> = ({ checked, onChange, label }) => {
  return (
    <div className="flex items-center gap-3 cursor-pointer" onClick={() => onChange(!checked)}>
      <div className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ease-in-out ${checked ? 'bg-brand-orange' : 'bg-gray-200'}`}>
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition duration-200 ease-in-out ${checked ? 'translate-x-6' : 'translate-x-1'}`}
        />
      </div>
      {label && <span className="text-sm font-medium text-gray-700 select-none">{label}</span>}
    </div>
  );
};