export function Window({ title, children, className = "", as: Tag = "section", ...rest }) {
  return (
    <Tag className={`window ${className}`} {...rest}>
      {title && <h2 className="window-title">{title}</h2>}
      {children}
    </Tag>
  );
}
