import React, { useState, useEffect, useRef } from 'react';
import {
  StyleSheet,
  View,
  SafeAreaView,
  StatusBar,
  TextInput,
  TouchableOpacity,
  Text,
  ActivityIndicator,
  Alert,
  Modal
} from 'react-native';
import { WebView } from 'react-native-webview';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Audio } from 'expo-av';

const DEFAULT_SERVER_URL = 'http://192.168.1.100:8000';

export default function App() {
  const [serverUrl, setServerUrl] = useState(DEFAULT_SERVER_URL);
  const [inputUrl, setInputUrl] = useState(DEFAULT_SERVER_URL);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const webViewRef = useRef(null);

  useEffect(() => {
    loadSavedUrl();
    requestPermissions();
  }, []);

  const loadSavedUrl = async () => {
    try {
      const saved = await AsyncStorage.getItem('mj_server_url');
      if (saved) {
        setServerUrl(saved);
        setInputUrl(saved);
      }
    } catch (e) {
      console.warn('Could not load saved URL', e);
    }
  };

  const saveUrl = async () => {
    let clean = inputUrl.trim();
    if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
      clean = 'http://' + clean;
    }
    setServerUrl(clean);
    setIsModalOpen(false);
    try {
      await AsyncStorage.setItem('mj_server_url', clean);
      if (webViewRef.current) {
        webViewRef.current.reload();
      }
    } catch (e) {
      Alert.alert('Error', 'Failed to save URL');
    }
  };

  const requestPermissions = async () => {
    try {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: true,
      });
    } catch (e) {
      console.warn('Permissions warning', e);
    }
  };

  const handleMessage = (event) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'tts_play') {
        playAudio(data.url);
      }
    } catch (e) {}
  };

  const playAudio = async (url) => {
    try {
      const { sound } = await Audio.Sound.createAsync({ uri: url }, { shouldPlay: true });
      await sound.playAsync();
    } catch (e) {
      console.warn('Audio play error', e);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#030712" />

      {/* Top Sci-Fi Header */}
      <View style={styles.topBar}>
        <View style={styles.brandRow}>
          <Text style={styles.brandLogo}>⚡ MJ JARVIS</Text>
          <Text style={styles.brandBadge}>MOBILE</Text>
        </View>
        <TouchableOpacity style={styles.settingsBtn} onPress={() => setIsModalOpen(true)}>
          <Text style={styles.settingsBtnText}>⚙️ URL</Text>
        </TouchableOpacity>
      </View>

      {/* Embedded High-Performance WebView */}
      <WebView
        ref={webViewRef}
        source={{ uri: serverUrl }}
        style={styles.webView}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        mediaPlaybackRequiresUserAction={false}
        allowsInlineMediaPlayback={true}
        onLoadStart={() => setIsLoading(true)}
        onLoadEnd={() => setIsLoading(false)}
        onMessage={handleMessage}
        renderError={() => (
          <View style={styles.errorContainer}>
            <Text style={styles.errorTitle}>⚡ Connection Standby</Text>
            <Text style={styles.errorSub}>
              Could not reach MJ Backend at:{'\n'}
              <Text style={{ color: '#00f0ff' }}>{serverUrl}</Text>
            </Text>
            <TouchableOpacity style={styles.retryBtn} onPress={() => setIsModalOpen(true)}>
              <Text style={styles.retryBtnText}>Configure IP / ngrok URL</Text>
            </TouchableOpacity>
          </View>
        )}
      />

      {/* Loading Overlay */}
      {isLoading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#00f0ff" />
          <Text style={styles.loadingText}>Initializing JARVIS Neural Core...</Text>
        </View>
      )}

      {/* Server IP / ngrok Configuration Modal */}
      <Modal visible={isModalOpen} transparent={true} animationType="slide">
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>⚡ Bridge Server Configuration</Text>
            <Text style={styles.modalSub}>
              Enter your Laptop's Wi-Fi IP (e.g. 192.168.1.100:8000) or secure ngrok tunnel URL:
            </Text>
            <TextInput
              style={styles.input}
              value={inputUrl}
              onChangeText={setInputUrl}
              placeholder="http://192.168.1.100:8000 or https://xyz.ngrok.io"
              placeholderTextColor="#64748b"
              autoCapitalize="none"
              autoCorrect={false}
            />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.modalCancel} onPress={() => setIsModalOpen(false)}>
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalSave} onPress={saveUrl}>
                <Text style={styles.modalSaveText}>Save & Connect</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#030712',
  },
  topBar: {
    height: 48,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    backgroundColor: '#030712',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 240, 255, 0.25)',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  brandLogo: {
    color: '#00f0ff',
    fontWeight: '900',
    fontSize: 15,
    letterSpacing: 1,
  },
  brandBadge: {
    color: '#ff7700',
    fontSize: 10,
    fontWeight: '700',
    marginLeft: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
    backgroundColor: 'rgba(255, 119, 0, 0.15)',
    borderRadius: 4,
    borderWidth: 1,
    borderColor: 'rgba(255, 119, 0, 0.4)',
  },
  settingsBtn: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(0, 240, 255, 0.4)',
    backgroundColor: 'rgba(0, 240, 255, 0.1)',
  },
  settingsBtnText: {
    color: '#00f0ff',
    fontSize: 12,
    fontWeight: '700',
  },
  webView: {
    flex: 1,
    backgroundColor: '#030712',
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(3, 7, 18, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#00f0ff',
    marginTop: 16,
    fontSize: 14,
    letterSpacing: 1,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#030712',
  },
  errorTitle: {
    fontSize: 20,
    color: '#ff7700',
    fontWeight: '800',
    marginBottom: 8,
  },
  errorSub: {
    color: '#94a3b8',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  retryBtn: {
    backgroundColor: 'rgba(0, 240, 255, 0.15)',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#00f0ff',
  },
  retryBtnText: {
    color: '#00f0ff',
    fontWeight: '700',
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalCard: {
    width: '100%',
    backgroundColor: '#080f1e',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: '#00f0ff',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#00f0ff',
    marginBottom: 8,
  },
  modalSub: {
    color: '#94a3b8',
    fontSize: 13,
    marginBottom: 16,
    lineHeight: 18,
  },
  input: {
    backgroundColor: '#030712',
    borderWidth: 1,
    borderColor: 'rgba(0, 240, 255, 0.4)',
    borderRadius: 8,
    padding: 12,
    color: '#fff',
    fontSize: 14,
    marginBottom: 20,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
  },
  modalCancel: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  modalCancelText: {
    color: '#94a3b8',
    fontWeight: '600',
  },
  modalSave: {
    backgroundColor: '#00f0ff',
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 8,
  },
  modalSaveText: {
    color: '#030712',
    fontWeight: '800',
  },
});
