<!--
   - Copyright (C) 2020 Julian Valentin, LTeX Development Community
   -
   - This Source Code Form is subject to the terms of the Mozilla Public
   - License, v. 2.0. If a copy of the MPL was not distributed with this
   - file, You can obtain one at https://mozilla.org/MPL/2.0/.
   -->

# mformat: Code Formatter for MATLAB, written in Python

mformat is a code formatter for MATLAB, written in Python. It is not finished yet.

## Limitations

Currently, only a subset of MATLAB is supported. The following language features are not supported:

- Multi-row arrays `[...; ...]` and cell arrays `{...; ...}`
- Tilde `~` to omit input/output argument
- Transpose operator `'`
- Comma `,` to terminate statements
- Command-style calls like `hold on`

Additionally, the following formatting features are on the wishlist:

- Wrap long lines
- Allow single-line blocks
