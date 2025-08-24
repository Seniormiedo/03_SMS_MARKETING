import {
  ChartBarIcon,
  CpuChipIcon,
  SignalIcon,
  SparklesIcon
} from "@heroicons/react/24/outline";
import React, { useEffect } from "react";
import { ChartsGrid } from "../../components/analytics/ChartsGrid";
import { MetricsCards } from "../../components/analytics/MetricsCards";
import { LoadingSpinner } from "../../components/common/LoadingSpinner";
import { QuickActions } from "../../components/common/QuickActions";
import { RecentActivity } from "../../components/common/RecentActivity";
import { useAppDispatch, useAppSelector } from "../../hooks/redux";
import { fetchContactStats } from "../../store/slices/contactsSlice";

export const DashboardPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const contactsState = useAppSelector((state) => state.contacts);
  const { stats, loading, error } = contactsState;

  useEffect(() => {
    dispatch(fetchContactStats());
  }, [dispatch]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-slate-300 text-sm">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <div className="bg-red-500/10 backdrop-blur-sm border border-red-500/20 rounded-xl p-8 max-w-md w-full">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500/20 rounded-full mb-4">
              <SignalIcon className="w-8 h-8 text-red-400" />
            </div>
            <h3 className="text-xl font-semibold text-red-200 mb-2">
              Error de Conexión
            </h3>
            <p className="text-red-300/80 text-sm mb-6">
              {error}
            </p>
            <button
              onClick={() => dispatch(fetchContactStats())}
              className="bg-red-500 hover:bg-red-600 text-white px-6 py-2 rounded-lg font-medium transition-colors duration-200"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Modern Header with Glass Effect */}
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
          <div className="md:flex md:items-center md:justify-between">
            <div className="min-w-0 flex-1">
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-12 h-12 bg-purple-500/20 rounded-xl">
                  <SparklesIcon className="w-7 h-7 text-purple-300" />
                </div>
                <div>
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-purple-300 bg-clip-text text-transparent">
                    SMS Marketing Platform
                  </h1>
                  <p className="mt-2 text-slate-300 text-lg">
                    Control total de tus campañas de marketing
                  </p>
                </div>
              </div>
            </div>
            <div className="mt-6 md:mt-0 md:ml-8">
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-px rounded-xl">
                <div className="bg-slate-900/50 backdrop-blur-sm rounded-xl px-6 py-3">
                  <QuickActions />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricsCards stats={stats} />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Charts Section - Takes 2 columns */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <ChartBarIcon className="w-6 h-6 text-purple-300" />
                  <h2 className="text-xl font-semibold text-white">Analytics</h2>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm text-green-300">Live</span>
                </div>
              </div>
              <ChartsGrid stats={stats} />
            </div>
          </div>

          {/* Sidebar - Takes 1 column */}
          <div className="space-y-6">

            {/* System Status Card */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center space-x-3 mb-6">
                <CpuChipIcon className="w-6 h-6 text-emerald-300" />
                <h3 className="text-lg font-semibold text-white">Estado del Sistema</h3>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse"></div>
                    <span className="text-slate-300 font-medium">Base de Datos</span>
                  </div>
                  <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs font-semibold border border-emerald-500/30">
                    Saludable
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
                    <span className="text-slate-300 font-medium">Bot Telegram</span>
                  </div>
                  <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs font-semibold border border-blue-500/30">
                    Activo
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                  <div className="flex items-center space-x-3">
                    <div className="w-3 h-3 bg-amber-400 rounded-full animate-pulse"></div>
                    <span className="text-slate-300 font-medium">Validadores</span>
                  </div>
                  <span className="px-3 py-1 bg-amber-500/20 text-amber-300 rounded-full text-xs font-semibold border border-amber-500/30">
                    En Desarrollo
                  </span>
                </div>
              </div>

              {/* Performance Indicators */}
              <div className="mt-6 pt-6 border-t border-white/10">
                <h4 className="text-sm font-semibold text-slate-300 mb-4">Performance</h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">CPU</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full w-[45%] bg-gradient-to-r from-green-400 to-emerald-500 rounded-full"></div>
                      </div>
                      <span className="text-xs text-slate-300">45%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-400">Memoria</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-16 h-2 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full w-[72%] bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full"></div>
                      </div>
                      <span className="text-xs text-slate-300">72%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl">
              <RecentActivity />
            </div>
          </div>
        </div>

        {/* Footer Info */}
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-sm text-slate-300">
                <span className="font-semibold text-white">31.8M</span> contactos activos
              </div>
              <div className="w-px h-4 bg-white/20"></div>
              <div className="text-sm text-slate-300">
                Última actualización: {new Date().toLocaleString('es-ES')}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-emerald-300 font-medium">Sistema Operativo</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
