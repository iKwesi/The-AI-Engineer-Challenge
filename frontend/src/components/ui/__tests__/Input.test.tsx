import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Input } from '../Input';

describe('Input Component', () => {
  const mockOnChange = jest.fn();
  const mockOnBlur = jest.fn();
  const mockOnFocus = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
    mockOnBlur.mockClear();
    mockOnFocus.mockClear();
  });

  // Test basic rendering
  it('renders input element', () => {
    render(<Input />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  // Test with placeholder
  it('renders with placeholder', () => {
    render(<Input placeholder="Enter text here" />);
    expect(screen.getByPlaceholderText('Enter text here')).toBeInTheDocument();
  });

  // Test with value
  it('renders with value', () => {
    render(<Input value="test value" onChange={mockOnChange} />);
    expect(screen.getByDisplayValue('test value')).toBeInTheDocument();
  });

  // Test onChange functionality
  it('calls onChange when value changes', () => {
    render(<Input onChange={mockOnChange} />);
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'new value' } });
    expect(mockOnChange).toHaveBeenCalledTimes(1);
  });

  // Test onFocus functionality
  it('calls onFocus when input is focused', () => {
    render(<Input onFocus={mockOnFocus} />);
    const input = screen.getByRole('textbox');
    fireEvent.focus(input);
    expect(mockOnFocus).toHaveBeenCalledTimes(1);
  });

  // Test onBlur functionality
  it('calls onBlur when input loses focus', () => {
    render(<Input onBlur={mockOnBlur} />);
    const input = screen.getByRole('textbox');
    fireEvent.blur(input);
    expect(mockOnBlur).toHaveBeenCalledTimes(1);
  });

  // Test different input types
  it('renders password input type', () => {
    render(<Input type="password" />);
    const input = screen.getByDisplayValue('');
    expect(input).toHaveAttribute('type', 'password');
  });

  it('renders email input type', () => {
    render(<Input type="email" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'email');
  });

  it('defaults to text input type', () => {
    render(<Input />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'text');
  });

  // Test disabled state
  it('renders disabled state correctly', () => {
    render(<Input disabled />);
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
    expect(input).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed');
  });

  // Test error state
  it('renders error state correctly', () => {
    render(<Input error />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-red-500', 'bg-red-50');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  // Test error message
  it('displays error message when provided', () => {
    render(<Input error errorMessage="This field is required" />);
    expect(screen.getByText('This field is required')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  // Test label functionality
  it('renders with label', () => {
    render(<Input label="Username" />);
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
  });

  // Test required field indicator
  it('shows required indicator when required', () => {
    render(<Input label="Username" required />);
    expect(screen.getByText('*')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveAttribute('required');
  });

  // Test custom className
  it('applies custom className', () => {
    render(<Input className="custom-class" />);
    expect(screen.getByRole('textbox')).toHaveClass('custom-class');
  });

  // Test accessibility attributes
  it('has proper accessibility attributes', () => {
    render(<Input />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('focus-visible:outline-none', 'focus-visible:ring-2', 'focus-visible:ring-ring');
  });

  // Test label association
  it('properly associates label with input', () => {
    render(<Input label="Email Address" id="email" />);
    const input = screen.getByRole('textbox');
    const label = screen.getByText('Email Address');
    expect(label).toHaveAttribute('for', 'email');
    expect(input).toHaveAttribute('id', 'email');
  });

  // Test error message accessibility
  it('properly associates error message with input', () => {
    render(<Input error errorMessage="Invalid email" id="email" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-describedby', 'email-error');
    expect(screen.getByText('Invalid email')).toHaveAttribute('id', 'email-error');
  });

  // Test focus behavior
  it('can receive focus', () => {
    render(<Input />);
    const input = screen.getByRole('textbox');
    input.focus();
    expect(input).toHaveFocus();
  });

  // Test name attribute
  it('sets name attribute correctly', () => {
    render(<Input name="username" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('name', 'username');
  });
});
