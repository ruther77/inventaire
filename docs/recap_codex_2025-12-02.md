# Récap des artefacts générés le 2025-12-02

## Journaux Codex
- `docs/codex_assistant_messages_2025-12-02.txt` : tous les messages de l’assistant (texte) pour le 02/12.
- `docs/codex_toolcalls_2025-12-02.txt` : sorties brutes contenant les appels d’outils (ToolCall: shell_command).
- `docs/codex_shell_commands_2025-12-02.txt` : tentatives de liste des commandes shell (peut être vide selon la structure des logs).
- `docs/codex_shell_calls_2025-12-02.txt` : idem, tentative alternative (peut comporter des erreurs jq si les logs sont hétérogènes).

## Modifications de code (aujourd’hui)
- Liste des fichiers modifiés avec horodatage : `docs/codex_code_files_modified_2025-12-02_with_times.txt`.
- Diff complet du worktree actuel : `docs/codex_code_diffs_2025-12-02.txt` (toutes les lignes modifiées).
- Statistiques + état du repo : `docs/codex_code_changes_2025-12-02.txt` (diffstat + `git status --short`).

## Divers
- Sauvegardes/restauration : `docs/epicerie_backup_20251202_154053.sql` (+ `.gz`).
- Événements Docker du jour : `docs/docker-events-today.txt`.

## Sauvegarde la plus récente de /monprojet
- Dump complet horodaté (15h40 env.) : `docs/epicerie_backup_20251202_154053.sql` (et la version compressée `.gz`).
- Sauvegarde locale avant restauration (dump rapide) : `backups/backup_pre_restore.sql` (générée dans le conteneur db, copiée sous `/backups`).
- Aucune sauvegarde disponible autour de 09h : aucun fichier de dump daté en début de matinée n’a été trouvé (`ls docs | grep backup`), et `backups/backup_pre_restore.sql` est un fichier vide (0 o).

### Pour reprendre le diagnostic après plantage
1. Consulte la liste horodatée des fichiers modifiés : `docs/codex_code_files_modified_2025-12-02_with_times.txt`.
2. Ouvre le diff complet pour voir les lignes touchées : `docs/codex_code_diffs_2025-12-02.txt`.
3. Si besoin d’un fichier précis : `git diff -- <chemin_du_fichier>`.
4. Vérifie l’état du repo avant action : `git status`.
