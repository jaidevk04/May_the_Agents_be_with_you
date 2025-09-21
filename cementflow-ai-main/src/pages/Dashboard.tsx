import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Activity,
  Zap,
  TrendingUp,
  AlertTriangle,
  Circle,
  ArrowUp,
  ArrowDown
} from "lucide-react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer } from "recharts";

// Helper to fetch data
const fetchData = async (url) => {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      console.error(`Error fetching ${url}: ${response.statusText}`);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching ${url}:`, error);
    return null;
  }
};

const Dashboard = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [plantStatus, setPlantStatus] = useState({
    status: "Loading...",
    energyEfficiency: 0,
    productionRate: 0,
    activeAlerts: 0,
  });
  const [processStatus, setProcessStatus] = useState({
    rawMaterials: { status: "Loading...", value: "N/A" },
    clinkerization: { status: "Loading...", value: "N/A" },
    qualityControl: { status: "Loading...", value: "N/A" },
  });
  const [liveAlerts, setLiveAlerts] = useState([]);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    const fetchAllData = async () => {
      // Fetch from cemet_plant_api (port 8001) for overall status
      const agentStatus = await fetchData("http://localhost:8001/agent/status");
      if (agentStatus && agentStatus.performance_data) {
        setPlantStatus({
          status: agentStatus.agent_status.includes("Online") ? "Optimal" : "Warning",
          energyEfficiency: agentStatus.performance_data.average_energy_efficiency_kwh_per_ton,
          productionRate: agentStatus.performance_data.average_production_tph,
          activeAlerts: agentStatus.performance_data.total_anomalies_detected,
        });
        setProcessStatus(prev => ({ ...prev, rawMaterials: { status: "Active", value: `${agentStatus.performance_data.average_production_tph.toFixed(2)} tph` } }));
      } else {
        setPlantStatus({ status: "Offline", energyEfficiency: 0, productionRate: 0, activeAlerts: 0 });
        setProcessStatus(prev => ({ ...prev, rawMaterials: { status: "Offline", value: "N/A" } }));
      }

      // Fetch from cement-plant (port 8000) for clinkerization alerts
      const clinkerStatus = await fetchData("http://localhost:8000/simulation-status");
      if (clinkerStatus && clinkerStatus.events) {
        const formattedAlerts = clinkerStatus.events.slice(-5).map((event, index) => ({
          id: index,
          timestamp: new Date(event.timestamp).toLocaleString(),
          severity: event.alert ? "warning" : "info",
          source: "Clinkerization",
          message: event.alert || `Prediction: ${event.prediction.toFixed(4)}`,
        }));
        setLiveAlerts(formattedAlerts.reverse());
        if (clinkerStatus.events.length > 0) {
          const lastEvent = clinkerStatus.events[clinkerStatus.events.length - 1];
          setProcessStatus(prev => ({ ...prev, clinkerization: { status: lastEvent.alert ? "Optimizing" : "Stable", value: `Free Lime: ${lastEvent.prediction.toFixed(2)}%` } }));
        }
      } else {
        setProcessStatus(prev => ({ ...prev, clinkerization: { status: "Offline", value: "N/A" } }));
      }

      // Fetch from qc_backend (port 8002) for quality control status
      const qcState = await fetchData("http://localhost:8002/state/current");
      if (qcState) {
        setProcessStatus(prev => ({ ...prev, qualityControl: { status: "Stable", value: `LSF: ${qcState.LSF_est.toFixed(2)}` } }));
      } else {
        setProcessStatus(prev => ({ ...prev, qualityControl: { status: "Offline", value: "N/A" } }));
      }
    };

    fetchAllData(); // Initial fetch
    const dataInterval = setInterval(fetchAllData, 5000); // Refresh every 5 seconds

    return () => {
      clearInterval(timer);
      clearInterval(dataInterval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">Plant Operations Dashboard</h1>
            <p className="text-muted-foreground">
              Real-time monitoring and AI-powered optimization
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Current Time</p>
            <p className="text-xl font-mono text-foreground">
              {currentTime.toLocaleTimeString()}
            </p>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Plant Status</CardTitle>
            <Activity className={`h-4 w-4 ${plantStatus.status === 'Optimal' ? 'text-success' : 'text-warning'}`} />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <Circle className={`h-3 w-3 ${plantStatus.status === 'Optimal' ? 'fill-success text-success' : 'fill-warning text-warning'} animate-pulse`} />
              <div className={`text-2xl font-bold ${plantStatus.status === 'Optimal' ? 'text-success' : 'text-warning'}`}>{plantStatus.status}</div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Energy Efficiency</CardTitle>
            <Zap className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{plantStatus.energyEfficiency.toFixed(2)} kWh/ton</div>
            <Progress value={plantStatus.energyEfficiency} max={25} className="mt-2" />
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Production Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{plantStatus.productionRate.toFixed(2)} tph</div>
            <Progress value={plantStatus.productionRate} max={200} className="mt-2" />
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">{liveAlerts.filter(a => a.severity === 'warning').length}</div>
            <div className="text-sm text-muted-foreground mt-1">
              Live from simulation
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Process Status Overview */}
        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Process Status Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
              <div>
                <h3 className="font-medium text-foreground">Raw Materials & Grinding</h3>
                <p className="text-sm text-muted-foreground mt-1">{processStatus.rawMaterials.value}</p>
              </div>
              <div className="flex items-center space-x-2">
                <Circle className={`h-3 w-3 ${processStatus.rawMaterials.status === 'Active' ? 'fill-success text-success' : 'fill-destructive text-destructive'}`} />
                <Badge variant="secondary" className={`${processStatus.rawMaterials.status === 'Active' ? 'bg-success/20 text-success' : 'bg-destructive/20 text-destructive'}`}>{processStatus.rawMaterials.status}</Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
              <div>
                <h3 className="font-medium text-foreground">Clinkerization</h3>
                <p className="text-sm text-muted-foreground mt-1">{processStatus.clinkerization.value}</p>
              </div>
              <div className="flex items-center space-x-2">
                <Circle className={`h-3 w-3 ${processStatus.clinkerization.status === 'Stable' ? 'fill-success text-success' : processStatus.clinkerization.status === 'Optimizing' ? 'fill-warning text-warning animate-pulse' : 'fill-destructive text-destructive'}`} />
                <Badge variant="secondary" className={`${processStatus.clinkerization.status === 'Stable' ? 'bg-success/20 text-success' : processStatus.clinkerization.status === 'Optimizing' ? 'bg-warning/20 text-warning' : 'bg-destructive/20 text-destructive'}`}>{processStatus.clinkerization.status}</Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
              <div>
                <h3 className="font-medium text-foreground">Quality Control</h3>
                <p className="text-sm text-muted-foreground mt-1">{processStatus.qualityControl.value}</p>
              </div>
              <div className="flex items-center space-x-2">
                <Circle className={`h-3 w-3 ${processStatus.qualityControl.status === 'Stable' ? 'fill-success text-success' : 'fill-destructive text-destructive'}`} />
                <Badge variant="secondary" className={`${processStatus.qualityControl.status === 'Stable' ? 'bg-success/20 text-success' : 'bg-destructive/20 text-destructive'}`}>{processStatus.qualityControl.status}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Live Alerts Feed */}
        <Card className="lg:col-span-2 bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Live Alert & Recommendation Feed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {liveAlerts.length > 0 ? liveAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-4 rounded-lg border-l-4 ${
                    alert.severity === "warning"
                      ? "bg-warning/10 border-warning"
                      : "bg-primary/10 border-primary"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <Badge
                        variant="secondary"
                        className={
                          alert.severity === "warning"
                            ? "bg-warning/20 text-warning"
                            : "bg-primary/20 text-primary"
                        }
                      >
                        {alert.source}
                      </Badge>
                      <span className="text-xs text-muted-foreground font-mono">
                        {alert.timestamp}
                      </span>
                    </div>
                    <Badge
                      variant="outline"
                      className={
                        alert.severity === "warning"
                          ? "border-warning text-warning"
                          : "border-primary text-primary"
                      }
                    >
                      {alert.severity.toUpperCase()}
                    </Badge>
                  </div>
                  <p className="text-sm text-foreground">{alert.message}</p>
                </div>
              )) : <p className="text-muted-foreground">No alerts from the clinkerization simulation yet. Make sure the simulation is started on the Clinkerization Control page.</p>}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
