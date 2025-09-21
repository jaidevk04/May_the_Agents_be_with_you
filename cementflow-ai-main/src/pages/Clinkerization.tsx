import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Play,
  Flame,
  Thermometer,
  Gauge,
  Fuel,
  Bot,
  AlertTriangle,
  Clock,
  Loader2
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface PlantState {
  kiln_speed: number;
  fuel_rate: number;
  raw_mix_composition: string;
  cooler_speed: number;
  coal_feed_rate: number;
}

interface SimulationEvent {
  timestamp: string;
  prediction: number;
  alert?: string;
  llm_response?: any;
}

const Clinkerization = () => {
  const [isSimulating, setIsSimulating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [plantState, setPlantState] = useState<PlantState | null>(null);
  const [simulationEvents, setSimulationEvents] = useState<SimulationEvent[]>([]);
  const { toast } = useToast();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = async () => {
    try {
      const stateRes = await fetch("http://localhost:8000/plant_state");
      if (stateRes.ok) {
        const stateData = await stateRes.json();
        setPlantState(stateData);
      } else {
        console.error("Failed to fetch plant state");
      }

      const statusRes = await fetch("http://localhost:8000/simulation-status");
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        if (statusData.events) {
          setSimulationEvents(statusData.events.slice().reverse());
        }
        // If simulation is running on backend but not in UI, sync it
        if (statusData.is_running && !isSimulating) {
          setIsSimulating(true);
        }
      } else {
        console.error("Failed to fetch simulation status");
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      toast({
        title: "Connection Error",
        description: "Could not connect to the clinkerization service.",
        variant: "destructive",
      });
      // Stop polling if there's a connection error
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      setIsSimulating(false);
    }
  };

  useEffect(() => {
    // Initial fetch to get current state
    fetchData();

    if (isSimulating) {
      intervalRef.current = setInterval(fetchData, 3000); // Poll every 3 seconds
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isSimulating]);

  const startSimulation = async () => {
    setIsLoading(true);
    toast({
      title: "Starting Simulation",
      description: "Please wait...",
    });

    try {
      const response = await fetch("http://localhost:8000/start-simulation", {
        method: "POST",
      });
      if (response.ok) {
        const data = await response.json();
        toast({
          title: "Simulation Started",
          description: data.message || "Autonomous clinkerization control is now active.",
        });
        setIsSimulating(true);
      } else {
        const errorData = await response.json();
        toast({
          title: "Failed to Start Simulation",
          description: errorData.message || "An error occurred.",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Could not connect to the simulation service.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (value: number, min: number, max: number) => {
    if (value < min || value > max) return "text-danger";
    if (value < min * 1.1 || value > max * 0.9) return "text-warning";
    return "text-success";
  };

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Autonomous Clinkerization Control</h1>
        <p className="text-muted-foreground">
          AI-powered kiln control and real-time process optimization
        </p>
      </div>

      {/* Control Panel */}
      <Card className="mb-6 bg-card/50 backdrop-blur border-border shadow-card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flame className="h-5 w-5" />
            Simulation Control Panel
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground mb-2">
                Start autonomous clinkerization simulation with AI-powered process control
              </p>
              <div className="flex items-center gap-4">
                <Badge variant="secondary" className={`${isSimulating ? "bg-success/20 text-success" : "bg-muted text-muted-foreground"}`}>
                  {isSimulating ? "Simulation Active" : "Simulation Stopped"}
                </Badge>
                <Badge variant="secondary" className="bg-primary/20 text-primary">
                  AI Agent: Ready
                </Badge>
              </div>
            </div>
            <Button
              onClick={startSimulation}
              disabled={isSimulating || isLoading}
              className="bg-gradient-primary hover:opacity-90 text-primary-foreground"
              size="lg"
            >
              {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
              {isLoading ? "Starting..." : isSimulating ? "Simulation Running" : "Start"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Live Plant State */}
        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Live Plant State</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {!plantState ? <p className="text-muted-foreground">Waiting for plant data...</p> : (
              <>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Gauge className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Kiln Speed</span>
                    </div>
                    <span className={`text-lg font-bold ${getStatusColor(plantState.kiln_speed, 3.0, 6.0)}`}>
                      {plantState.kiln_speed.toFixed(1)} RPM
                    </span>
                  </div>
                  <Progress value={(plantState.kiln_speed / 7) * 100} className="h-2" />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Fuel className="h-4 w-4 text-secondary" />
                      <span className="text-sm font-medium">Fuel Rate</span>
                    </div>
                    <span className={`text-lg font-bold ${getStatusColor(plantState.fuel_rate, 90, 110)}`}>
                      {plantState.fuel_rate.toFixed(1)}
                    </span>
                  </div>
                  <Progress value={(plantState.fuel_rate / 150) * 100} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Thermometer className="h-4 w-4 text-warning" />
                      <span className="text-sm font-medium">Cooler Speed</span>
                    </div>
                    <span className={`text-lg font-bold ${getStatusColor(plantState.cooler_speed, 2.5, 3.5)}`}>
                      {plantState.cooler_speed.toFixed(1)}
                    </span>
                  </div>
                  <Progress value={(plantState.cooler_speed / 5) * 100} className="h-2" />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Flame className="h-4 w-4 text-danger" />
                      <span className="text-sm font-medium">Coal Feed Rate</span>
                    </div>
                    <span className={`text-lg font-bold ${getStatusColor(plantState.coal_feed_rate, 18, 22)}`}>
                      {plantState.coal_feed_rate.toFixed(1)}
                    </span>
                  </div>
                  <Progress value={(plantState.coal_feed_rate / 30) * 100} className="h-2" />
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Live Simulation Feed */}
        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Live Simulation Feed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {simulationEvents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Clock className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold text-foreground mb-2">Waiting for Simulation</h3>
                  <p className="text-muted-foreground">
                    Start the simulation to see real-time AI analysis and control decisions
                  </p>
                </div>
              ) : (
                simulationEvents.map((event, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border-l-4 ${
                      event.alert
                        ? "bg-warning/10 border-warning"
                        : event.llm_response
                        ? "bg-primary/10 border-primary"
                        : "bg-success/10 border-success"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-muted-foreground font-mono">
                        {new Date(event.timestamp).toLocaleString()}
                      </span>
                      {event.alert && (
                        <div className="flex items-center gap-1">
                          <AlertTriangle className="h-4 w-4 text-warning" />
                          <Badge variant="outline" className="border-warning text-warning text-xs">
                            ALERT
                          </Badge>
                        </div>
                      )}
                      {event.llm_response && (
                        <div className="flex items-center gap-1">
                          <Bot className="h-4 w-4 text-primary" />
                          <Badge variant="outline" className="border-primary text-primary text-xs">
                            AI ACTION
                          </Badge>
                        </div>
                      )}
                    </div>

                    <p className="text-sm text-foreground mb-2">Free Lime Prediction: {event.prediction.toFixed(4)}</p>

                    {event.alert && (
                      <div className="mt-2 p-2 bg-warning/20 rounded text-sm">
                        <strong className="text-warning">Alert:</strong> {event.alert}
                      </div>
                    )}

                    {event.llm_response && (
                      <div className="mt-3 p-3 bg-primary/20 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Bot className="h-4 w-4 text-primary" />
                          <span className="text-sm font-medium text-primary">AI Agent Response</span>
                        </div>
                        <div className="space-y-2">
                          <div>
                            <span className="text-xs font-medium text-foreground">Action:</span>
                            <p className="text-sm text-foreground mt-1">{event.llm_response.action}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Clinkerization;
