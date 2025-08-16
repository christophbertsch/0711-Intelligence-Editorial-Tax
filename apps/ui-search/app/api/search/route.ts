export async function POST(req: Request) {
  try {
    const body = await req.json();
    
    const searchPayload = {
      collection: process.env.COLLECTION || "vertical_generic",
      query: body.query,
      k: body.k || 20,
      hybrid: body.hybrid !== false,
      return: body.return || ["title", "snippet", "score", "citations", "source_url", "doc_type"]
    };

    const response = await fetch(`${process.env.SEVEN011_BASE_URL}/v1/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.SEVEN011_API_KEY}`
      },
      body: JSON.stringify(searchPayload)
    });

    if (!response.ok) {
      throw new Error(`Search API error: ${response.status}`);
    }

    const data = await response.json();
    
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      }
    });

  } catch (error) {
    console.error('Search API error:', error);
    return new Response(
      JSON.stringify({ error: 'Search failed', details: error.message }), 
      { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}