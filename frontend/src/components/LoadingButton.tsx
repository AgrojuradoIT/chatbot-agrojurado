import React from 'react';
import Loader from './Loader';

type LoadingButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
	loading?: boolean;
	spinnerSize?: number;
	spinnerColor?: string;
	loadingText?: React.ReactNode;
};

const LoadingButton: React.FC<LoadingButtonProps> = ({
	loading = false,
	spinnerSize = 16,
	spinnerColor = '#ffffff',
	loadingText = 'Procesando...',
	disabled,
	children,
	...rest
}) => {
	const isDisabled = Boolean(disabled) || loading;

	return (
		<button {...rest} disabled={isDisabled}>
			{loading && <Loader size={spinnerSize} color={spinnerColor} />}
			{loading ? loadingText : children}
		</button>
	);
};

export default LoadingButton;


