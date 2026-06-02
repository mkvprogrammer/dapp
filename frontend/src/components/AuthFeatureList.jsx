import { AUTH_FEATURES } from './icons/Icons';

export default function AuthFeatureList({ listClassName, itemClassName, iconClassName }) {
  const listCls = listClassName || 'LoginPage__features';
  const itemCls = itemClassName || 'LoginPage__feature';
  const iconCls = iconClassName || 'LoginPage__feature-icon';

  return (
    <ul className={listCls}>
      {AUTH_FEATURES.map(({ Icon, label }) => (
        <li key={label} className={itemCls}>
          <span className={iconCls}>
            <Icon />
          </span>
          {label}
        </li>
      ))}
    </ul>
  );
}
