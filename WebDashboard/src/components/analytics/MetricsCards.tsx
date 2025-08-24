import {
  CheckCircleIcon,
  ClockIcon,
  DocumentTextIcon,
  UsersIcon,
} from "@heroicons/react/24/outline";
import React from "react";
import { Icon } from "../common/Icon";

interface MetricsCardsProps {
  stats: {
    totalContacts: number;
    contactsByState: Record<string, number>;
    contactsByLada: Record<string, number>;
    recentExtractions: number;
  };
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ stats }) => {
  // Provide default values if stats is undefined
  const safeStats = stats || {
    totalContacts: 0,
    contactsByState: {},
    contactsByLada: {},
    recentExtractions: 0,
  };

  const metrics = [
    {
      name: "Total Contactos",
      value: safeStats.totalContacts.toLocaleString(),
      icon: UsersIcon,
      change: "+2.5%",
      changeType: "increase" as const,
      description: "este mes",
      color: "blue",
      bgGradient: "from-blue-500/20 to-cyan-500/20",
      iconBg: "bg-blue-500/20",
      iconColor: "text-blue-300",
    },
    {
      name: "Estados Cubiertos",
      value: Object.keys(safeStats.contactsByState).length.toString(),
      icon: DocumentTextIcon,
      change: "+1",
      changeType: "increase" as const,
      description: "nuevo estado",
      color: "green",
      bgGradient: "from-emerald-500/20 to-green-500/20",
      iconBg: "bg-emerald-500/20",
      iconColor: "text-emerald-300",
    },
    {
      name: "Extracciones Recientes",
      value: safeStats.recentExtractions.toString(),
      icon: CheckCircleIcon,
      change: "+12%",
      changeType: "increase" as const,
      description: "esta semana",
      color: "purple",
      bgGradient: "from-purple-500/20 to-pink-500/20",
      iconBg: "bg-purple-500/20",
      iconColor: "text-purple-300",
    },
    {
      name: "Tasa de Validación",
      value: "94.2%",
      icon: ClockIcon,
      change: "+0.8%",
      changeType: "increase" as const,
      description: "precisión mejorada",
      color: "orange",
      bgGradient: "from-amber-500/20 to-orange-500/20",
      iconBg: "bg-amber-500/20",
      iconColor: "text-amber-300",
    },
  ];

  return (
    <>
      {metrics.map((metric, index) => (
        <div
          key={metric.name}
          className="relative group cursor-pointer animate-slide-up"
          style={{ animationDelay: `${index * 100}ms` }}
        >
          {/* Card with Glass Morphism Effect */}
          <div className={`bg-gradient-to-br ${metric.bgGradient} backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 hover:scale-105`}>

            {/* Icon and Title */}
            <div className="flex items-center justify-between mb-4">
              <div className={`flex items-center justify-center w-12 h-12 ${metric.iconBg} rounded-xl ring-2 ring-white/10`}>
                <Icon icon={metric.icon} size="md" className={`${metric.iconColor}`} />
              </div>

              {/* Live indicator */}
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
                <span className="text-xs text-emerald-300 font-medium">Live</span>
              </div>
            </div>

            {/* Value */}
            <div className="mb-3">
              <h3 className="text-sm font-medium text-slate-300 mb-1">
                {metric.name}
              </h3>
              <p className="text-3xl font-bold text-white">
                {metric.value}
              </p>
            </div>

            {/* Change indicator */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    metric.changeType === "increase"
                      ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                      : "bg-red-500/20 text-red-300 border border-red-500/30"
                  }`}
                >
                  {metric.change}
                </span>
                <span className="text-xs text-slate-400">{metric.description}</span>
              </div>
            </div>

            {/* Hover glow effect */}
            <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-purple-500/10 blur-xl -z-10"></div>
          </div>
        </div>
      ))}
    </>
  );
};
