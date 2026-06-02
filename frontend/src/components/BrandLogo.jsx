import { images } from '../assets/paths';

export default function BrandLogo({ className, width = 40, height = 40 }) {
  return (
    <img className={className} src={images.logo} alt="" width={width} height={height} />
  );
}
