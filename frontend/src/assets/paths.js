/** Пути к изображениям из вёрстки (frontend/assets/images). */
export const images = {
  logo: '/assets/images/logo.png',
  logoSvg: '/assets/images/logo.svg',
  loginIllustration: '/assets/images/login-illustration.png',
  registrationIllustration: '/assets/images/regill.JPG',
};

export const auctionBanners = [
  '/assets/images/auction-math-consultation.png',
  '/assets/images/auction-smart-space.png',
  '/assets/images/auction-physics-lab.png',
  '/assets/images/auction-3d-printer.png',
  '/assets/images/auction-algorithms-seminar.png',
];

export function auctionBannerFor(id) {
  const idx = Math.abs(Number(id) || 0) % auctionBanners.length;
  return auctionBanners[idx];
}
