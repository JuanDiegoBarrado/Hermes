# Hermes

## ⚠️ Modo servidor (`serve`) en Windows

El modo servidor está pensado para Linux (p. ej. una Raspberry Pi). En Windows funciona,
pero **la parada no es inmediata**: entre revisiones, Hermes espera hasta el próximo disparo
o, como mucho, `HERMES_WAKEUP_SECONDS` (900 s por defecto), y en Windows esa espera no se
interrumpe con Ctrl+C. La parada se atiende cuando acaba la espera, así que puede tardar
hasta `HERMES_WAKEUP_SECONDS`.

Si lo ejecutas en Windows:

- Para salir al momento, cierra la ventana o mata el proceso. Si en ese momento se está
  ejecutando un job, se corta a medias.
- O baja `HERMES_WAKEUP_SECONDS` en el `.env`: la parada tardará como mucho eso.

En Linux, Ctrl+C y SIGTERM (`docker stop`, systemd...) cortan la espera al instante.
