import React from 'react';

export interface ButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  type = 'button',
  className = '',
}) => {
  const baseClasses = 'px-4 py-2 rounded-lg font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-accent text-accent-text hover:bg-accent-hover disabled:hover:bg-accent',
    secondary: 'bg-transparent border border-border text-text-primary hover:bg-gray-100 disabled:hover:bg-transparent',
  };
  
  const disabledClasses = 'opacity-50 cursor-not-allowed';
  
  const buttonClasses = [
    baseClasses,
    variantClasses[variant],
    disabled ? disabledClasses : '',
    className,
  ].join(' ').trim();

  return (
    <button
      type={type}
      className={buttonClasses}
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      aria-disabled={disabled}
    >
      {children}
    </button>
  );
};

export default Button;
