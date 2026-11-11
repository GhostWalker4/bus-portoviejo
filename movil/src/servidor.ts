import Constants from 'expo-constants';

/**
 * Dirección del servidor Django.
 *
 * 1. Si existe EXPO_PUBLIC_SERVIDOR_URL (en movil/.env.local), se usa esa.
 * 2. Si no, se toma la IP de la computadora que está corriendo `npx expo start`
 *    (la misma que usa Expo Go para cargar la app) y se le pone el puerto 8000.
 *    Así funciona en el celular sin configurar nada, siempre que el servidor
 *    se haya iniciado con `python manage.py runserver 0.0.0.0:8000`.
 */
export function urlServidor(): string {
  const configurada = process.env.EXPO_PUBLIC_SERVIDOR_URL;
  if (configurada) return configurada.replace(/\/$/, '');

  const hostExpo = Constants.expoConfig?.hostUri?.split(':')[0];
  return `http://${hostExpo ?? 'localhost'}:8000`;
}

export type Salud = { estado: string; servicio: string; hora: string };

export async function consultarSalud(): Promise<Salud> {
  const control = new AbortController();
  const espera = setTimeout(() => control.abort(), 5000);
  try {
    const r = await fetch(`${urlServidor()}/api/salud/`, { signal: control.signal });
    if (!r.ok) throw new Error(`El servidor respondió ${r.status}`);
    return (await r.json()) as Salud;
  } finally {
    clearTimeout(espera);
  }
}
