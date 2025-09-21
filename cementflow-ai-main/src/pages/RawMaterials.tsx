import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Play,
  Loader2,
  Zap,
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  Settings
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const RawMaterials = () => {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationResults, setOptimizationResults] = useState<any>(null);
  const { toast } = useToast();

  const runOptimization = async () => {
    setIsOptimizing(true);
    setOptimizationResults(null);
    toast({
      title: "Optimization Started",
      description: "AI analysis in progress...",
    });

    try {
      const response = await fetch("http://localhost:8001/agent/optimize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const results = await response.json();
      
      // Extract the nested optimization results
      if (results.agent_analysis && results.agent_analysis.optimization_results) {
        setOptimizationResults(results.agent_analysis.optimization_results);
        toast({
          title: "Optimization Complete",
          description: "Analysis results are now available.",
        });
      } else {
        throw new Error("Invalid data structure in API response");
      }

    } catch (error) {
      console.error("Optimization failed:", error);
      toast({
        title: "Optimization Failed",
        description: "Unable to connect to optimization service or parse results.",
        variant: "destructive",
      });
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Raw Materials & Grinding Optimization</h1>
        <p className="text-muted-foreground">
          AI-powered optimization for raw material composition and grinding efficiency
        </p>
      </div>

      {/* Control Panel */}
      <Card className="mb-6 bg-card/50 backdrop-blur border-border shadow-card-elevated">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Optimization Control Panel
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground mb-2">
                Run comprehensive AI analysis for raw materials and grinding optimization
              </p>
              <div className="flex items-center gap-4">
                <Badge variant="secondary" className="bg-primary/20 text-primary">
                  AI Agent: Ready
                </Badge>
                <Badge variant="secondary" className="bg-success/20 text-success">
                  Mill Status: Active
                </Badge>
              </div>
            </div>
            <Button
              onClick={runOptimization}
              disabled={isOptimizing}
              className="bg-gradient-primary hover:opacity-90 text-primary-foreground"
              size="lg"
            >
              {isOptimizing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Run New Optimization Analysis
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Display */}
      {optimizationResults && (
        <Card className="bg-card/50 backdrop-blur border-border shadow-card-elevated">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Optimization Results</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="summary" className="w-full">
              <TabsList className="grid w-full grid-cols-6">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="raw-materials">Raw Materials</TabsTrigger>
                <TabsTrigger value="grinding">Grinding</TabsTrigger>
                <TabsTrigger value="energy">Energy</TabsTrigger>
                <TabsTrigger value="maintenance">Maintenance</TabsTrigger>
                <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
              </TabsList>

              <TabsContent value="summary" className="mt-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <Card className="bg-success/10 border-success">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Plant Status</p>
                          <p className="text-xl font-bold text-success">{optimizationResults.plant_status}</p>
                        </div>
                        <CheckCircle2 className="h-6 w-6 text-success" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-primary/10 border-primary">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Energy Efficiency</p>
                          <p className="text-xl font-bold text-primary">{optimizationResults.energy_efficiency_kwh_per_ton.toFixed(2)} kWh/ton</p>
                        </div>
                        <Zap className="h-6 w-6 text-primary" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-secondary/10 border-secondary">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Potential Savings</p>
                          <p className="text-xl font-bold text-secondary">${optimizationResults.potential_savings.annual_savings_usd.toFixed(2)}/year</p>
                        </div>
                        <TrendingDown className="h-6 w-6 text-secondary" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-foreground mb-4">Priority Actions</h3>
                  <div className="space-y-3">
                    {optimizationResults.priority_actions.map((action: string, index: number) => (
                      <div key={index} className="flex items-start gap-3 p-3 bg-muted/20 rounded-lg">
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium mt-0.5">
                          {index + 1}
                        </div>
                        <p className="text-sm text-foreground">{action}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="raw-materials" className="mt-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Raw Material Optimizations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-foreground leading-relaxed whitespace-pre-wrap">{optimizationResults.raw_material_optimizations.summary}</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="grinding" className="mt-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Grinding Optimizations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-foreground leading-relaxed whitespace-pre-wrap">{optimizationResults.grinding_optimizations.summary}</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="energy" className="mt-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Energy Optimizations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-foreground leading-relaxed whitespace-pre-wrap">{optimizationResults.energy_optimizations.summary}</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="maintenance" className="mt-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Maintenance Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-foreground leading-relaxed whitespace-pre-wrap">{optimizationResults.maintenance_recommendations.summary}</p>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="anomalies" className="mt-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Detected Anomalies</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {optimizationResults.anomalies_detected.length > 0 ? optimizationResults.anomalies_detected.map((anomaly: string, index: number) => (
                        <div key={index} className="flex items-center gap-3 p-3 bg-warning/10 rounded-lg border border-warning/20">
                          <AlertTriangle className="h-5 w-5 text-warning" />
                          <p className="text-foreground">{anomaly}</p>
                        </div>
                      )) : <p className="text-muted-foreground">No anomalies detected.</p>}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {!optimizationResults && !isOptimizing && (
        <Card className="bg-card/30 backdrop-blur border-dashed border-2 border-border">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Settings className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No Optimization Data</h3>
            <p className="text-muted-foreground text-center">
              Run an optimization analysis to view detailed results and recommendations
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default RawMaterials;
