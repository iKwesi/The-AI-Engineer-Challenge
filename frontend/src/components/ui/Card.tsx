import React from 'react';
import { cn } from '@/lib/utils';

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

// Card Header Component
export interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  children,
  className = ''
}) => {
  return (
    <div className={cn("flex flex-col space-y-1.5 p-6", className)}>
      {children}
    </div>
  );
};

// Card Title Component
export interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

export const CardTitle: React.FC<CardTitleProps> = ({
  children,
  className = ''
}) => {
  return (
    <h3 className={cn("text-2xl font-semibold leading-none tracking-tight", className)}>
      {children}
    </h3>
  );
};

// Card Description Component
export interface CardDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export const CardDescription: React.FC<CardDescriptionProps> = ({
  children,
  className = ''
}) => {
  return (
    <p className={cn("text-sm text-muted-foreground", className)}>
      {children}
    </p>
  );
};

// Card Content Component
export interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export const CardContent: React.FC<CardContentProps> = ({
  children,
  className = ''
}) => {
  return (
    <div className={cn("p-6 pt-0", className)}>
      {children}
    </div>
  );
};

export default Card;
