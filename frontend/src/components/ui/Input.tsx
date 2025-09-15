import React from 'react';

export interface InputProps {
  type?: 'text' | 'password' | 'email' | 'number';
  placeholder?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  error?: boolean;
  errorMessage?: string;
  label?: string;
  id?: string;
  name?: string;
  required?: boolean;
  className?: string;
}

export const Input: React.FC<InputProps> = ({
  type = 'text',
  placeholder,
  value,
  onChange,
  onBlur,
  onFocus,
  disabled = false,
  error = false,
  errorMessage,
  label,
  id,
  name,
  required = false,
  className = '',
}) => {
  const inputId = id || name || `input-${Math.random().toString(36).substr(2, 9)}`;
  
  const baseClasses = 'w-full px-3 py-2 border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1';
  const normalClasses = 'border-border bg-container text-text-primary focus:border-accent';
  const errorClasses = 'border-red-500 bg-red-50 text-text-primary focus:border-red-500 focus:ring-red-500';
  const disabledClasses = 'opacity-50 cursor-not-allowed bg-gray-100';
  
  const inputClasses = [
    baseClasses,
    error ? errorClasses : normalClasses,
    disabled ? disabledClasses : '',
    className,
  ].join(' ').trim();

  return (
    <div className="w-full">
      {label && (
        <label 
          htmlFor={inputId}
          className="block text-sm font-medium text-text-primary mb-1"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <input
        id={inputId}
        name={name}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        onFocus={onFocus}
        disabled={disabled}
        required={required}
        className={inputClasses}
        aria-invalid={error}
        aria-describedby={error && errorMessage ? `${inputId}-error` : undefined}
      />
      {error && errorMessage && (
        <p 
          id={`${inputId}-error`}
          className="mt-1 text-sm text-red-600"
          role="alert"
        >
          {errorMessage}
        </p>
      )}
    </div>
  );
};

export default Input;
