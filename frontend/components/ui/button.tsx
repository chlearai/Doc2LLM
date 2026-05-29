import { useState, useRef, useEffect, type ButtonHTMLAttributes, type ReactNode, type MouseEvent } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  loading?: boolean;
  icon?: ReactNode;
};

interface Ripple {
  id: number;
  x: number;
  y: number;
}

export function Button({
  className = "",
  variant = "primary",
  loading = false,
  icon,
  children,
  disabled,
  onMouseEnter,
  onMouseLeave,
  onClick,
  ...props
}: ButtonProps) {
  const [hoverCoords, setHoverCoords] = useState({ x: 0, y: 0 });
  const [ripples, setRipples] = useState<Ripple[]>([]);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Clean up ripples after animation finishes (600ms)
  useEffect(() => {
    if (ripples.length === 0) return;
    const timeout = setTimeout(() => {
      setRipples([]);
    }, 600);
    return () => clearTimeout(timeout);
  }, [ripples]);

  function handleMouseMove(e: MouseEvent<HTMLButtonElement>) {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setHoverCoords({ x, y });
    }
  }

  const handleMouseEnter = (e: MouseEvent<HTMLButtonElement>) => {
    handleMouseMove(e);
    if (onMouseEnter) onMouseEnter(e);
  };

  const handleMouseLeave = (e: MouseEvent<HTMLButtonElement>) => {
    handleMouseMove(e);
    if (onMouseLeave) onMouseLeave(e);
  };

  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const newRipple = { id: Date.now(), x, y };
      setRipples((prev) => [...prev, newRipple]);
    }
    if (onClick) onClick(e);
  };

  return (
    <button
      ref={buttonRef}
      className={`button button-${variant} ${className}`.trim()}
      disabled={disabled || loading}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onMouseMove={handleMouseMove}
      onClick={handleClick}
      {...props}
    >
      {icon}
      <span className="btn-text">{loading ? "Working" : children}</span>
      
      {/* Position-aware Hover background element */}
      <span 
        className="btn-hover-bg" 
        style={{ left: hoverCoords.x, top: hoverCoords.y }}
      />

      {/* Click Ripples */}
      {ripples.map((ripple) => (
        <span
          key={ripple.id}
          className="btn-ripple"
          style={{ left: ripple.x, top: ripple.y }}
        />
      ))}
    </button>
  );
}
