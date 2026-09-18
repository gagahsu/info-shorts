import React, {createContext, useContext} from 'react';
import type {Theme} from './theme';
import {themes} from './theme';
import type {ContentKind} from './types';

type Ctx = {theme: Theme; kind: ContentKind};

const ThemeCtx = createContext<Ctx>({theme: themes.neutral, kind: 'generic'});

export const ThemeProvider: React.FC<React.PropsWithChildren<Ctx>> = ({theme, kind, children}) => (
  <ThemeCtx.Provider value={{theme, kind}}>{children}</ThemeCtx.Provider>
);

export const useTheme = (): Ctx => useContext(ThemeCtx);
