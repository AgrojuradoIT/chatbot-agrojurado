import React from 'react';
import '../styles/Loader.css';

type LoaderProps = {
	/** Tamaño del spinner en píxeles */
	size?: number;
	/** Color del spinner */
	color?: string;
	/** Clases adicionales opcionales */
	className?: string;
};

export const Loader: React.FC<LoaderProps> = ({ size = 16, color = '#ffffff', className }) => {
	const borderWidth = Math.max(2, Math.floor(size / 8));
	const style: React.CSSProperties = {
		width: size,
		height: size,
		border: `${borderWidth}px solid rgba(255, 255, 255, 0.3)`,
		borderTopColor: color,
	};

	return <span className={`loader ${className || ''}`} style={style} />;
};

export default Loader;


