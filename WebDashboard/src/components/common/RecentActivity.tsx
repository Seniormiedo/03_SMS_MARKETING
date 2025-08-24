import {
  CheckBadgeIcon,
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
  UserPlusIcon,
} from "@heroicons/react/24/outline";
import { formatDistanceToNow } from "date-fns";
import React from "react";

interface Activity {
  id: string;
  type: "extraction" | "contact_added" | "validation" | "error";
  message: string;
  timestamp: Date;
  details?: string;
}

export const RecentActivity: React.FC = () => {
  // Mock data - will be replaced with real data from API
  const activities: Activity[] = [
    {
      id: "1",
      type: "extraction",
      message: "Nueva extracción completada: Estado SINALOA",
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      details: "1,500 contactos extraídos",
    },
    {
      id: "2",
      type: "contact_added",
      message: "Importación masiva de contactos",
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      details: "2,300 nuevos contactos",
    },
    {
      id: "3",
      type: "validation",
      message: "Validación WhatsApp completada",
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      details: "850 números validados",
    },
    {
      id: "4",
      type: "extraction",
      message: "Exportación generada: Municipio JALISCO",
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      details: "3,200 contactos en formato XLSX",
    },
    {
      id: "5",
      type: "error",
      message: "Límite de velocidad alcanzado en validador Instagram",
      timestamp: new Date(Date.now() - 60 * 60 * 1000),
      details: "Cambio automático a método de respaldo",
    },
  ];

  const getActivityIcon = (type: Activity["type"]) => {
    const iconMap = {
      extraction: DocumentArrowDownIcon,
      contact_added: UserPlusIcon,
      validation: CheckBadgeIcon,
      error: ExclamationTriangleIcon,
    };
    return iconMap[type];
  };

  const getActivityColor = (type: Activity["type"]) => {
    const colorMap = {
      extraction: {
        bg: "bg-blue-500/20",
        icon: "text-blue-300",
        border: "border-blue-500/30",
      },
      contact_added: {
        bg: "bg-emerald-500/20",
        icon: "text-emerald-300",
        border: "border-emerald-500/30",
      },
      validation: {
        bg: "bg-purple-500/20",
        icon: "text-purple-300",
        border: "border-purple-500/30",
      },
      error: {
        bg: "bg-red-500/20",
        icon: "text-red-300",
        border: "border-red-500/30",
      },
    };
    return colorMap[type];
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-white flex items-center space-x-3">
          <DocumentArrowDownIcon className="w-6 h-6 text-blue-300" />
          <span>Actividad Reciente</span>
        </h3>
        <button className="text-sm text-purple-300 hover:text-purple-200 transition-colors font-medium">
          Ver todo
        </button>
      </div>

      <div className="space-y-4">
        {activities.map((activity) => {
          const Icon = getActivityIcon(activity.type);
          const colors = getActivityColor(activity.type);

          return (
            <div
              key={activity.id}
              className="group relative bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-all duration-300"
            >
              <div className="flex items-start space-x-4">
                <div className={`flex items-center justify-center w-10 h-10 ${colors.bg} ${colors.border} border rounded-xl flex-shrink-0`}>
                  <Icon className={`w-5 h-5 ${colors.icon}`} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white group-hover:text-purple-200 transition-colors">
                        {activity.message}
                      </p>
                      <p className="mt-1 text-xs text-slate-400">
                        {formatDistanceToNow(activity.timestamp, {
                          addSuffix: true,
                        })}
                      </p>
                    </div>

                    <div className="flex items-center space-x-1 ml-4">
                      <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></div>
                    </div>
                  </div>

                  {activity.details && (
                    <div className="mt-2 text-xs text-slate-300 bg-white/5 rounded-lg px-3 py-2 border border-white/5">
                      {activity.details}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 pt-4 border-t border-white/10">
        <div className="flex items-center justify-center space-x-2">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
          <span className="text-xs text-slate-300">Actualización automática cada 30 segundos</span>
        </div>
      </div>
    </div>
  );
};
