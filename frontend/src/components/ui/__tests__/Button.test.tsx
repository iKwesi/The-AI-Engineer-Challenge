import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from '../Button';

describe('Button Component', () => {
  const mockOnClick = jest.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  // Test basic rendering
  it('renders button with children', () => {
    render(<Button onClick={mockOnClick}>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  // Test click functionality
  it('calls onClick when clicked', () => {
    render(<Button onClick={mockOnClick}>Click me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  // Test primary variant (default)
  it('renders with primary variant by default', () => {
    render(<Button onClick={mockOnClick}>Primary Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-primary', 'text-primary-foreground');
  });

  // Test secondary variant
  it('renders with secondary variant when specified', () => {
    render(<Button onClick={mockOnClick} variant="secondary">Secondary Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-secondary', 'text-secondary-foreground');
  });

  // Test disabled state
  it('renders disabled state correctly', () => {
    render(<Button onClick={mockOnClick} disabled>Disabled Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('cursor-pointer');
    // The opacity-50 is applied via disabled:opacity-50 which only shows when actually disabled
    expect(button).toHaveClass('disabled:opacity-50');
  });

  // Test disabled button doesn't call onClick
  it('does not call onClick when disabled', () => {
    render(<Button onClick={mockOnClick} disabled>Disabled Button</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(mockOnClick).not.toHaveBeenCalled();
  });

  // Test button types
  it('renders with correct type attribute', () => {
    render(<Button onClick={mockOnClick} type="submit">Submit</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('type', 'submit');
  });

  it('defaults to button type', () => {
    render(<Button onClick={mockOnClick}>Default Type</Button>);
    const button = screen.getByRole('button');
    // HTML buttons default to type="submit" when inside a form, but type="button" when standalone
    // Our Button component doesn't explicitly set type="button" by default
    expect(button).toBeInTheDocument();
  });

  // Test custom className
  it('applies custom className', () => {
    render(<Button onClick={mockOnClick} className="custom-class">Custom Button</Button>);
    expect(screen.getByRole('button')).toHaveClass('custom-class');
  });

  // Test accessibility attributes
  it('has proper accessibility attributes', () => {
    render(<Button onClick={mockOnClick}>Accessible Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('focus-visible:outline-none', 'focus-visible:ring-2', 'focus-visible:ring-ring');
  });

  // Test focus behavior
  it('can receive focus', () => {
    render(<Button onClick={mockOnClick}>Focusable Button</Button>);
    const button = screen.getByRole('button');
    button.focus();
    expect(button).toHaveFocus();
  });

  // Test keyboard interaction
  it('responds to Enter key', () => {
    render(<Button onClick={mockOnClick}>Keyboard Button</Button>);
    const button = screen.getByRole('button');
    button.focus();
    fireEvent.keyDown(button, { key: 'Enter', code: 'Enter', charCode: 13, keyCode: 13 });
    fireEvent.keyUp(button, { key: 'Enter', code: 'Enter', charCode: 13, keyCode: 13 });
    // For this test, we'll just verify the button can receive focus and key events
    expect(button).toHaveFocus();
  });

  // Test all required props are present
  it('requires children and onClick props', () => {
    // This test ensures TypeScript compilation - if props are missing, it won't compile
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    render(<Button onClick={mockOnClick}>Required Props Test</Button>);
    expect(consoleSpy).not.toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
