import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';

import './i18n';

import RsmLayout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider } from './contexts/AuthContext';
import Accueil from './pages/Accueil';
import Recherche from './pages/Recherche';
import Inscriptions from './pages/Inscriptions';
import DetailInscription from './pages/DetailInscription';
import Audit from './pages/Audit';
import Statistiques from './pages/Statistiques';
import PartenairesBancaires from './pages/PartenairesBancaires';
import TableauBordGreffe from './pages/TableauBordGreffe';
import MonEspace from './pages/MonEspace';
import Connexion from './pages/Connexion';
import ChangerMotDePasse from './pages/ChangerMotDePasse';
import GestionCategoriesBiens from './pages/GestionCategoriesBiens';

import FormulaireInscription from './pages/FormulaireInscription';
import FormulairePrivilegeVendeur from './pages/FormulairePrivilegeVendeur';
import FormulaireReserveProprete from './pages/FormulaireReserveProprete';
import FormulaireCreditBail from './pages/FormulaireCreditBail';
import ChoixTypeSurete from './pages/ChoixTypeSurete';
import FormulaireModification from './pages/FormulaireModification';
import FormulaireRenouvellement from './pages/FormulaireRenouvellement';
import FormulaireRadiation from './pages/FormulaireRadiation';

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<RsmLayout />}>
              <Route path="/" element={<Accueil />} />
              <Route path="/recherche" element={<Recherche />} />
              <Route path="/inscriptions" element={<Inscriptions />} />
              <Route path="/inscriptions/:reference" element={<DetailInscription />} />
              <Route path="/audit" element={<Audit />} />
              <Route path="/statistiques" element={<Statistiques />} />
              <Route path="/partenaires-bancaires" element={<PartenairesBancaires />} />
              <Route path="/tableau-de-bord-greffe" element={<TableauBordGreffe />} />
              <Route path="/mon-espace" element={<MonEspace />} />
              <Route path="/connexion" element={<Connexion />} />
              <Route path="/changer-mot-de-passe" element={<ChangerMotDePasse />} />
              <Route path="/admin/categories-biens" element={<GestionCategoriesBiens />} />

              {/* Choix du type de sûreté + 4 parcours dédiés */}
              <Route path="/formulaires/inscription" element={<ChoixTypeSurete />} />
              <Route path="/formulaires/inscription/depot-surete" element={<FormulaireInscription />} />
              <Route path="/formulaires/inscription/privilege-vendeur" element={<FormulairePrivilegeVendeur />} />
              <Route path="/formulaires/inscription/reserve-propriete" element={<FormulaireReserveProprete />} />
              <Route path="/formulaires/inscription/credit-bail" element={<FormulaireCreditBail />} />
              <Route path="/formulaires/modification" element={<FormulaireModification />} />
              <Route path="/formulaires/renouvellement" element={<FormulaireRenouvellement />} />
              <Route path="/formulaires/radiation" element={<FormulaireRadiation />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}
