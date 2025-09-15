import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'small' | 'medium' | 'large';
  shadow?: boolean;
  [key: string]: unknown; // Allow any additional props like data-testid
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  padding = 'medium',
  shadow = true,
  ...rest
}) => {
  const baseClasses = 'bg-container rounded-lg border border-border';
  
  const paddingClasses = {
    none: '',
    small: 'p-3',
    medium: 'p-4',
    large: 'p-6',
  };
  
  const shadowClasses = shadow ? 'shadow-soft' : '';
  
  const cardClasses = [
    baseClasses,
    paddingClasses[padding],
    shadowClasses,
    className,
  ].join(' ').trim();

  return (
    <div className={cardClasses} {...rest}>
      {children}
    </div>
  );
};

export default Card;
