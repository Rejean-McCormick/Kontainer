# Third-party dependencies

The delivered source does not vendor dependencies; they are installed by the package manager.

| Component | Role | Upstream license to retain when distributing |
|---|---|---|
| PyNaCl | libsodium API | Apache-2.0 |
| libsodium | Native cryptographic primitives | ISC |
| argon2-cffi | Argon2 API | MIT |
| argon2-cffi-bindings | Bindings and Argon2 library | Consult MIT / CC0 / Apache notices in the distribution |
| CFFI | Native interface | MIT |
| pycparser | CFFI support parser | BSD |

Before redistributing native wheels, retain their exact notices and inventory included components. This table is a technical inventory, not legal advice.
