type IconProps = {
  name: string;
  className?: string;
  fill?: boolean;
};

export function Icon({ name, className = '', fill = false }: IconProps) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      aria-hidden
      style={
        fill
          ? { fontVariationSettings: "'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24" }
          : { fontVariationSettings: "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24" }
      }
    >
      {name}
    </span>
  );
}
