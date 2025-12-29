# 🧠 UDAC Portal

**Universal AI Continuity Browser**

A browser with a brain for AI platforms. UDAC Portal wraps AI chat interfaces (ChatGPT, Claude, Gemini, Perplexity, Copilot) in a WebView and provides cross-platform memory continuity.

## 🎯 The Problem It Solves

- You use multiple AI platforms
- Each one forgets who you are
- You repeat yourself constantly
- No continuity between sessions

## 💡 The Solution

UDAC Portal is a **browser-based approach** that:
1. Loads AI platforms in a WebView (your real accounts, real features)
2. Captures conversations via DOM observation
3. Builds cross-platform continuity memory
4. Injects context into your prompts automatically

**No accessibility services. No IME hacks. Just a smart browser.**

## ✨ Features

- ✅ **5 AI Platforms**: ChatGPT, Claude, Gemini, Perplexity, Copilot
- ✅ **Cross-Platform Memory**: What you discuss on Claude informs ChatGPT
- ✅ **Injection Strength Slider**: 0 (off) to 10 (full context)
- ✅ **Platform Isolation Mode**: Keep memories separate (Premium)
- ✅ **Data Trading**: Export anonymized patterns for storage credits
- ✅ **Voice Support**: Works with platforms' built-in voice features
- ✅ **100% Local**: Your data stays on your device
- ✅ **IVM Resilience Architecture**: Production-grade crash resistance (v1.0+)
- ✅ **Self-Healing Circuit Breakers**: Automatic error recovery
- ✅ **Memory Management**: No memory leaks, stable long-running sessions

## 📱 How It Works

```
┌─────────────────────────────────────────────────┐
│           UDAC Portal (Your Browser)            │
├─────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐    │
│  │          WebView (AI Platform)          │    │
│  │  - Your real account                    │    │
│  │  - All platform features                │    │
│  │  - Login handled by platform            │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │       UDAC Input Bar                    │    │
│  │  [Type your prompt here...] 🎤 [Send]  │    │
│  │  +47 tokens | ChatGPT, Claude context   │    │
│  └─────────────────────────────────────────┘    │
├─────────────────────────────────────────────────┤
│  Continuity Engine (DMC Brain)                  │
│  - Captures messages via JS injection           │
│  - Builds cross-platform memory                 │
│  - Enriches prompts with context                │
└─────────────────────────────────────────────────┘
```

## 🏗️ Architecture

### 6 Core Modules

1. **PlatformRegistry**: Defines AI platforms and DOM selectors
2. **PortalUI**: Home, Session, Settings screens (Kivy via `udac_portal.kivy_app`)
3. **SessionManager**: Routes events between components
4. **ContinuityEngine**: The DMC brain - compresses history, generates context
5. **ScriptBuilder**: Generates JS for DOM observation/injection
6. **InteractionLogger**: Stores interactions for data trading

### No Permissions Needed

Unlike the previous approach that required:
- ❌ Accessibility Service permissions
- ❌ Input Method Editor (IME) integration
- ❌ Complex service communication

UDAC Portal just needs:
- ✅ Internet permission (for WebView)
- ✅ That's it.

## 🚀 Getting Started

### Prerequisites

```bash
# Install Python 3.11+
python --version  # Should be 3.11+

# Install Briefcase (used for packaging metadata)
pip install briefcase
```

### Build Locally

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/udac-portal.git
cd udac-portal

# Create Android project
briefcase create android

# Build APK
briefcase build android

# Package APK
briefcase package android --adhoc

# APK will be in: build/udac_portal/android/gradle/app/build/outputs/apk/
```

### GitHub Actions

Push to `main` → GitHub Actions builds APK → Download from Actions artifacts

## 📦 Installation

1. Download APK from [Releases](https://github.com/YOUR_USERNAME/udac-portal/releases)
2. Install on Android (enable "Unknown Sources" if needed)
3. Open UDAC Portal
4. Select a platform
5. Log in with your normal account
6. Start chatting - continuity builds automatically!

## ⚙️ Settings

### Continuity Strength (0-10)

| Level | What Happens |
|-------|--------------|
| 0 | Continuity OFF - raw prompts only |
| 1-3 | Light context - recent summary |
| 4-6 | Medium context - cross-platform hints |
| 7-9 | Full context - user profile + topics |
| 10 | Maximum - everything we know |

### Platform Isolation (Premium)

- **OFF**: All platforms share memory (default)
- **ON**: Each platform has separate memory

### Data Trading

Export anonymized conversation patterns for storage credits:
- 100 patterns = 500 storage credits
- Only topic signatures, no raw text
- Completely opt-in

## 🔒 Privacy & Security

- **Local-first**: All data stored on device
- **Platform login**: Handled by platform, not UDAC
- **No password storage**: We never see your credentials
- **Anonymization**: Data trading uses topic signatures only
- **Open source**: Audit the code yourself

## 🗺️ Roadmap

- [ ] iOS build
- [ ] Desktop builds (macOS, Windows, Linux)
- [ ] Speech-to-text in UDAC input bar
- [ ] Custom platform definitions
- [ ] Cloud sync (encrypted, opt-in)
- [ ] Browser extension companion

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🤝 Contributing

Contributions welcome! Please read the code and open a PR.

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/udac-portal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/udac-portal/discussions)

---

**Made with 🧠 by Sunni | A browser with a brain for AI platforms**
