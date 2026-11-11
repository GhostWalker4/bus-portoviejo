import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { consultarSalud, urlServidor } from './src/servidor';

// Colores del proyecto (los mismos del roadmap).
const VERDE = '#0E3B3A';
const AMARILLO = '#F5B700';
const CREMA = '#FBF7EF';
const CORAL = '#E4573D';

type Estado =
  | { tipo: 'probando' }
  | { tipo: 'ok'; hora: string }
  | { tipo: 'error'; mensaje: string };

/**
 * Pantalla de la fase 0: solo comprueba que la app llega al servidor Django.
 * En la fase 4 se reemplaza por el mapa con las líneas y los buses.
 */
export default function App() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'probando' });

  const probar = useCallback(async () => {
    setEstado({ tipo: 'probando' });
    try {
      const s = await consultarSalud();
      setEstado({ tipo: 'ok', hora: new Date(s.hora).toLocaleTimeString('es-EC') });
    } catch (e) {
      setEstado({ tipo: 'error', mensaje: e instanceof Error ? e.message : String(e) });
    }
  }, []);

  useEffect(() => {
    probar();
  }, [probar]);

  return (
    <View style={styles.pantalla}>
      <Text style={styles.sello}>FASE 0</Text>
      <Text style={styles.titulo}>
        Bus{'\n'}
        <Text style={{ color: AMARILLO }}>Portoviejo</Text>
      </Text>
      <Text style={styles.sub}>Saber dónde viene tu bus y si te da tiempo de llegar a la parada.</Text>

      <View style={styles.tarjeta}>
        <Text style={styles.etiqueta}>Conexión con el servidor</Text>
        {estado.tipo === 'probando' && <ActivityIndicator color={VERDE} style={{ marginVertical: 8 }} />}
        {estado.tipo === 'ok' && <Text style={[styles.resultado, { color: VERDE }]}>Conectado · {estado.hora}</Text>}
        {estado.tipo === 'error' && (
          <>
            <Text style={[styles.resultado, { color: CORAL }]}>Sin conexión</Text>
            <Text style={styles.ayuda}>
              ¿Está corriendo «python manage.py runserver 0.0.0.0:8000» y están en el mismo Wi-Fi? ({estado.mensaje})
            </Text>
          </>
        )}
        <Text style={styles.url}>{urlServidor()}</Text>
        <Pressable style={styles.boton} onPress={probar}>
          <Text style={styles.botonTexto}>Probar de nuevo</Text>
        </Pressable>
      </View>

      <StatusBar style="light" />
    </View>
  );
}

const styles = StyleSheet.create({
  pantalla: { flex: 1, backgroundColor: VERDE, paddingHorizontal: 24, justifyContent: 'center' },
  sello: {
    alignSelf: 'flex-start', backgroundColor: AMARILLO, color: VERDE, fontWeight: '700',
    fontSize: 12, letterSpacing: 1.5, paddingHorizontal: 12, paddingVertical: 4, borderRadius: 20,
  },
  titulo: { color: '#fff', fontSize: 48, fontWeight: '800', lineHeight: 50, marginTop: 20 },
  sub: { color: '#CFE3DE', fontSize: 16, marginTop: 12, lineHeight: 22 },
  tarjeta: { backgroundColor: CREMA, borderRadius: 16, padding: 20, marginTop: 36 },
  etiqueta: { color: '#5C6967', fontSize: 13, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1 },
  resultado: { fontSize: 20, fontWeight: '700', marginTop: 8 },
  ayuda: { color: '#5C6967', fontSize: 13, marginTop: 6, lineHeight: 18 },
  url: { color: '#5C6967', fontSize: 12, marginTop: 10, fontFamily: 'monospace' },
  boton: { backgroundColor: VERDE, borderRadius: 10, paddingVertical: 12, alignItems: 'center', marginTop: 16 },
  botonTexto: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
