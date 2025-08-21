import React from "react";

interface IconProps {
  icon: React.ComponentType<any>;
  className?: string;
  size?: "sm" | "md" | "lg";
  [key: string]: any;
}

export const Icon: React.FC<IconProps> = ({
  icon: IconComponent,
  className = "",
  size = "md",
  ...props
}) => {
  const sizeStyles = {
    sm: { width: '1rem', height: '1rem' },
    md: { width: '1.5rem', height: '1.5rem' },
    lg: { width: '2rem', height: '2rem' }
  };

  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8"
  };

  return (
    <IconComponent
      className={`${sizeClasses[size]} ${className}`}
      style={{
        ...sizeStyles[size],
        maxWidth: sizeStyles[size].width,
        maxHeight: sizeStyles[size].height,
        minWidth: sizeStyles[size].width,
        minHeight: sizeStyles[size].height,
        flexShrink: 0,
        flexGrow: 0,
        display: 'inline-block',
        verticalAlign: 'middle'
      }}
      {...props}
    />
  );
};
