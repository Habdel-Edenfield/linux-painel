# PRD-003: Vitals Integration - Widget Refactoring

## Objective

Integrar Vitals GNOME Shell Extension como referência de design principal e refatorar widgets existentes (brightness-widget.py e obsidian-widget.py) para seguir padrões arquiteturais e estilísticos do Vitals.

## Success Criteria

- [ ] Documentação completa do Vitals criada (VITALS-DESIGN-REFERENCE.md)
- [ ] Skill de referência Vitals criada e funcional (skills/vitals-reference.md)
- [ ] Nova extensão GNOME Shell criada com módulos brightness e obsidian
- [ ] Ícones symbolic SVG criados seguindo padrões Vitals (16px)
- [ ] CSS stylesheet segue padrões de estilização Vitals
- [ ] GSettings schemas implementados para configurações persistentes
- [ ] Preferences dialog funcional com GTK widgets
- [ ] Hot sensors funcionam no panel (configurável)
- [ ] Menu open trigger refresh instantâneo de dados
- [ ] Ralph orquestração funciona com nova extensão
- [ ] Documentação atualizada (README, START_HERE, QUICK_START)
- [ ] Testes completados e passando
- [ ] Antigos widgets Python marcados como deprecated (mas mantidos)

## Background

### Current State

**Vitals Extension:** ✅ Instalado
- Local: `~/.local/share/gnome-shell/extensions/Vitals@CoreCoding.com/`
- Version: 73
- Architecture: GNOME Shell Extension nativa
- Follows: GNOME best practices, async polling, minimal CSS

**Existing Widgets:**
- **brightness-widget.py**: Python GTK + AyatanaAppIndicator3 (335 linhas)
  - Controla brilho/gamma via xrandr
  - Perfis configuráveis (normal, comfort, dark)
  - Config: `~/.config/brightness-widget/profiles.json`

- **obsidian-widget.py**: Python GTK + AyatanaAppIndicator3 (182 linhas)
  - Acesso rápido a vaults Obsidian
  - Scanneia diretórios por .obsidian
  - Usa protocolo obsidian://
  - Config: `~/.config/obsidian/obsidian.json`

- **foldermenu@user.local**: GNOME Shell extension (já OK)
  - Já usa arquitetura correta
  - Extensão existente mantida

### Problem Statement

Widgets Python usam AppIndicator/AyatanaAppIndicator3, que:
- Não se integra nativamente com GNOME Shell
- Não usa PanelMenu.Button nativo
- Tem estilização inconsistente
- Limita funcionalidades (hot sensors, instant refresh, etc.)

Vitals fornece excelente referência para:
- Arquitetura nativa GNOME Shell
- CSS minimalista e consistente
- Ícones symbolic SVG com temas
- GSettings configuration
- Async polling patterns
- UX patterns (hot sensors, instant refresh)

## Solution Design

### Architecture Decision

**Approach:** Converter brightness e obsidian para GNOME Shell Extensions

**Justification:**
- ✅ Consistência com Vitals (referência de design)
- ✅ Native GNOME integration
- ✅ Melhor performance (async polling)
- ✅ Hot sensors no panel
- ✅ GSettings configuration
- ✅ Instant refresh no menu open

**Trade-offs:**
- ❌ Curva de aprendizado JavaScript/GNOME Shell API
- ❌ Reescrever código existente
- ❌ Manter widgets Python como backup durante migração

### Extension Structure

```
/home/user/agent/extensions/system-tools@user.local/
├── extension.js               # Main extension file
├── prefs.js                  # Preferences dialog
├── prefs.ui                  # GTK UI definition
├── stylesheet.css             # Vitals-style CSS
├── metadata.json             # Extension metadata
├── schemas/
│   └── org.gnome.shell.extensions.system-tools.gschema.xml
└── icons/
    ├── original/             # Original theme
    │   ├── brightness-symbolic.svg
    │   └── obsidian-symbolic.svg
    └── gnome/              # GNOME theme (same files, different style)
```

### Modules Design

**Brightness Module:**
- PanelMenu.Button com hot sensor (brilho atual)
- Submenu com perfis: Normal (100%), Conforto (80%), Escuro (70%)
- xrandr control via `GLib.spawn_async()`
- GSettings: update-time, position, icon-style, default-profile, hot-show-brightness

**Obsidian Module:**
- PanelMenu.Button sem hot sensor (ou com vault favorito)
- Submenu com vaults encontrados
- obsidian:// protocolo via `GLib.spawn_async()`
- GSettings: vault-search-paths, hot-vault, icon-style, show-vaults-count

## Components

### Phase 1: Documentation (Priority 1)

**Deliverables:**
1. `specs/VITALS-DESIGN-REFERENCE.md` - Documentação completa do Vitals
   - Arquitetura e estrutura de arquivos
   - Sistema de ícones e temas
   - CSS classes e estilização
   - Menu structure e componentes
   - GSettings schema completo
   - Padrões de implementação a seguir

2. `skills/vitals-reference.md` - Skill de referência para Ralph agents
   - Como usar Vitals como padrão de design
   - Padrões a replicar
   - Anti-padrões a evitar
   - Checklists de design
   - Code templates

3. `specs/PRD-003-vitals-integration.md` - Este documento
   - Objetivos e success criteria
   - Background e problem statement
   - Solution design
   - Implementation roadmap
   - Testing strategy

### Phase 2: Extension Base (Priority 2)

**Deliverables:**
1. Extension skeleton com metadata.json
2. Main extension.js com VitalsMenuButton base
3. Basic stylesheet.css seguindo padrões Vitals
4. GSettings schema base
5. Icon directories (original/, gnome/)

### Phase 3: Brightness Module (Priority 2)

**Deliverables:**
1. brightness-symbolic.svg icon (tema original)
2. brightness-symbolic.svg icon (tema gnome)
3. Brightness submodule com:
   - Hot sensor no panel (brilho atual)
   - Submenu com 3 perfis
   - xrandr commands via GLib.spawn_async()
4. GSettings keys para brightness:
   - show-brightness (bool)
   - brightness-profiles (dict)
   - default-brightness-profile (string)
   - show-brightness-in-panel (bool)

### Phase 4: Obsidian Module (Priority 3)

**Deliverables:**
1. obsidian-symbolic.svg icon (tema original)
2. obsidian-symbolic.svg icon (tema gnome)
3. Obsidian submodule com:
   - Vault scanning (async)
   - Submenu com vaults encontrados
   - obsidian:// protocolo via GLib.spawn_async()
4. GSettings keys para obsidian:
   - show-obsidian (bool)
   - vault-search-paths (as - array)
   - hot-vault (string)
   - show-vaults-count (bool)

### Phase 5: Preferences (Priority 3)

**Deliverables:**
1. prefs.js com GTK4/Adw widgets
2. prefs.ui com layout da preferences window
3. Configurações para:
   - Icon style (original/gnome)
   - Position in panel
   - Show/hide brightness
   - Show/hide obsidian
   - Brightness profiles (add/edit/remove)
   - Vault search paths
   - Hot sensors configuration

### Phase 6: Ralph Integration (Priority 3)

**Deliverables:**
1. Atualizar `skills/brightness-control.md` para nova arquitetura
2. Atualizar `skills/obsidian-manager.md` para nova arquitetura
3. Atualizar `skills/system-widget-manager.md` para nova extensão
4. Adicionar hats e events ao `ralph.yml`:
   - design-coordinator hat
   - gnome-dev-specialist hat
   - widget.design event
   - widget.validate event
   - gnome.create event
   - gnome.modify event

### Phase 7: Testing (Priority 4)

**Deliverables:**
1. Test suite (script) validando:
   - Extensão carrega no GNOME Shell
   - Ícones symbolic carregam corretamente
   - Menu abre com refresh instantâneo
   - Brightness control funciona via xrandr
   - Obsidian vaults abrem corretamente
   - Configurações persistem via GSettings
   - CSS classes seguem padrões Vitals
   - Hot sensors funcionam no panel
   - Preferences dialog funciona
   - Ralph orquestração funciona

2. Manual testing checklist

### Phase 8: Documentation Updates (Priority 4)

**Deliverables:**
1. Atualizar `README.md` com seção Vitals
2. Atualizar `START_HERE.md` com instruções nova extensão
3. Atualizar `QUICK_START.md` com comandos nova extensão
4. Criar `MIGRATION-GUIDE.md` para transição dos widgets Python

## Dependencies

### External
- GNOME Shell 46+ (já instalado)
- xrandr (já instalado para brightness)
- Obsidian AppImage (já instalado em ~/Applications/)
- glib2, gio (bibliotecas GNOME - já instaladas)

### Internal
- Ralph workspace configurado (✅ COMPLETO)
- Vitals extension instalado (✅ COMPLETO)
- Documentação Vitals criada (🔄 IN PROGRESS)

## Implementation Roadmap

### Week 1: Documentation & Setup
- Day 1-2: Criar VITALS-DESIGN-REFERENCE.md
- Day 3: Criar skills/vitals-reference.md
- Day 4-5: Criar PRD-003-vitals-integration.md e aprovar

### Week 2: Extension Base
- Day 1-2: Criar estrutura base da extensão
- Day 3-4: Implementar stylesheet.css seguindo Vitals
- Day 5: Criar GSettings schema base

### Week 3: Brightness Module
- Day 1-2: Criar ícones symbolic SVG
- Day 3-4: Implementar brightness submodule
- Day 5: Testar xrandr commands via GLib

### Week 4: Obsidian Module
- Day 1-2: Criar ícones symbolic SVG
- Day 3-4: Implementar obsidian submodule
- Day 5: Testar obsidian:// protocolo

### Week 5: Preferences & Integration
- Day 1-2: Implementar prefs.js e prefs.ui
- Day 3-4: Atualizar skills do Ralph
- Day 5: Testar orquestração Ralph

### Week 6: Testing & Documentation
- Day 1-2: Criar test suite e executar
- Day 3-4: Atualizar documentação do workspace
- Day 5: Criar migration guide e finalizar

## Testing Strategy

### Unit Tests
- ✅ Icon loading returns correct path based on theme
- ✅ xrandr command generation correct
- ✅ obsidian:// URL generation correct
- ✅ GSettings keys have correct types

### Integration Tests
- ✅ Extension loads without errors
- ✅ Panel button appears
- ✅ Menu opens with correct structure
- ✅ Brightness submenu contains profiles
- ✅ Obsidian submenu contains vaults
- ✅ Settings changes trigger redraws

### End-to-End Tests
- ✅ User can change brightness via menu
- ✅ User can open Obsidian vault via menu
- ✅ Settings persist across reboots
- ✅ Hot sensors update in real-time
- ✅ Preferences dialog works
- ✅ Ralph can control extension via triggers

### Manual Testing
```bash
# Enable extension
gnome-extensions enable system-tools@user.local

# Check logs
journalctl -f -u gnome-shell

# Test brightness profile
# (click menu → brightness → select profile)

# Test obsidian vault
# (click menu → obsidian → select vault)

# Test preferences
# (click menu → preferences button)

# Test theme switching
# (preferences → change icon style → observe change)
```

## Risk Assessment

### High Risk
- **Curva de aprendizado JavaScript/GNOME Shell API**
  - Mitigation: Documentação completa, templates de código, referências

- **Breaking changes durante migração**
  - Mitigation: Manter widgets Python funcionando, deployment gradual

### Medium Risk
- **Compatibilidade com GNOME Shell 46+**
  - Mitigation: Testar extensivamente em diferentes versões

- **Ícones SVG não consistentes com Vitals**
  - Mitigation: Usar templates Vitals como base, revisar visualmente

### Low Risk
- **GSettings schema conflicts**
  - Mitigation: Usar namespace único (org.gnome.shell.extensions.system-tools)

- **Performance impact com extensão unificada**
  - Mitigation: Async polling, lazy loading

## Success Metrics

### Quantitative
- Extensão carrega em < 100ms
- Menu abre com refresh instantâneo (< 50ms)
- Hot sensors atualizam a cada 5s (configurável)
- Zero erros em journalctl após 24h de uso

### Qualitative
- UX consistente com Vitals (look & feel)
- Configurações intuitivas via Preferences dialog
- Migração transparente para usuário final
- Documentação clara para desenvolvimento futuro

## Notes

- **Vitals como Padrão:** Não copiar código, replicar padrões de design
- **Modularidade:** Manter módulos independentes (brightness, obsidian)
- **Backward Compatibility:** Manter widgets Python funcionando durante migração
- **Progressive Enhancement:** Implementar incrementalmente, testando cada fase
- **Princípios Ralph:** Fresh context, backpressure, signal-based steering

## Future Work (Post-Migration)

1. Criar widget calendar seguindo padrões Vitals
2. Implementar hot sensors customizáveis (drag & drop)
3. Adicionar suporte para múltiplos monitores
4. Criar unified settings dialog com abas
5. Implementar tema custom (além de original/gnome)
6. Adicionar animações sutis (fade in/out)
7. Criar sistema de notificações via eventos Ralph

---

**Status:** 🔄 IN PROGRESS
**Created:** 2026-03-02
**Last Updated:** 2026-03-02
