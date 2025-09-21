// Update this page (the content is just a fallback if you fail to update the page)

const Index = () => {
  // Redirect to dashboard
  window.location.href = "/";
  
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <h1 className="mb-4 text-4xl font-bold">Redirecting to CementAI Dashboard...</h1>
        <p className="text-xl text-muted-foreground">Loading industrial operations hub</p>
      </div>
    </div>
  );
};

export default Index;
