import React from 'react';
import { X, Lock } from 'lucide-react';

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const UpgradeModal: React.FC<UpgradeModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose}></div>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 relative z-10 animate-fade-in-up">
        <button 
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
            <X size={20} />
        </button>

        <div className="flex flex-col items-center text-center">
            <div className="w-16 h-16 bg-brand-orangeLight/50 rounded-full flex items-center justify-center mb-6 text-brand-orange">
                <Lock size={32} />
            </div>
            
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Oops! Limit Reached</h3>
            <p className="text-gray-600 mb-8 leading-relaxed">
                Your free download quota has been used up. <br/>
                Upgrade to Pro to unlock unlimited creations and higher quality models.
            </p>

            <button className="w-full bg-brand-black text-white font-bold py-3.5 rounded-xl hover:bg-gray-800 transition-colors shadow-lg mb-3">
                Upgrade Now
            </button>
            <button 
                onClick={onClose}
                className="text-sm text-gray-500 hover:text-gray-800 font-medium py-2"
            >
                Maybe Later
            </button>
        </div>
      </div>
    </div>
  );
};