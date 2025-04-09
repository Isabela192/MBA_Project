// Componente de Formulário para Criação de Usuários
const UserCreationForm = () => {
    // Estado para armazenar os dados do formulário
    const [formData, setFormData] = React.useState({
        document_id: '',
        name: '',
        username: '',
        email: '',
        user_type: 'client'
    });
    
    // Estado para mensagens de erro, sucesso e carregamento
    const [error, setError] = React.useState('');
    const [success, setSuccess] = React.useState('');
    const [loading, setLoading] = React.useState(false);

    // Função para lidar com mudanças nos campos do formulário
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    };

    // Função para lidar com o envio do formulário
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Resetar mensagens
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            // Enviando requisição para a API
            const response = await fetch(`/users/?user_type=${formData.user_type}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    document_id: formData.document_id,
                    name: formData.name,
                    username: formData.username,
                    email: formData.email
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Falha ao criar usuário');
            }

            // Sucesso
            setSuccess('Usuário criado com sucesso!');
            
            // Resetar formulário
            setFormData({
                document_id: '',
                name: '',
                username: '',
                email: '',
                user_type: 'client'
            });
        } catch (err) {
            // Erro
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <div className="header">
                <h1>SOLID Bank</h1>
                <p>Sistema de Cadastro de Usuários</p>
            </div>
            
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="document_id">Documento de Identificação:</label>
                    <input
                        type="text"
                        id="document_id"
                        name="document_id"
                        value={formData.document_id}
                        onChange={handleChange}
                        required
                        placeholder="Ex: 12345678901"
                    />
                </div>
                
                <div className="form-group">
                    <label htmlFor="name">Nome Completo:</label>
                    <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        placeholder="Ex: João da Silva"
                    />
                </div>
                
                <div className="form-group">
                    <label htmlFor="username">Nome de Usuário:</label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        required
                        placeholder="Ex: joaosilva"
                    />
                </div>
                
                <div className="form-group">
                    <label htmlFor="email">Email:</label>
                    <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        placeholder="Ex: joao@exemplo.com.br"
                    />
                </div>
                
                <div className="form-group">
                    <label htmlFor="user_type">Tipo de Usuário:</label>
                    <select
                        id="user_type"
                        name="user_type"
                        value={formData.user_type}
                        onChange={handleChange}
                    >
                        <option value="client">Cliente</option>
                        <option value="manager">Gerente</option>
                    </select>
                </div>
                
                <button type="submit" disabled={loading}>
                    {loading ? 'Processando...' : 'Criar Usuário'}
                </button>
                
                {error && <div className="error-message">{error}</div>}
                {success && <div className="success-message">{success}</div>}
            </form>
            
            <div className="form-footer">
                <p>Aplicação desenvolvida com padrões de projeto SOLID</p>
                <p>© {new Date().getFullYear()} - SOLID Bank</p>
            </div>
        </div>
    );
};

// Renderizar o componente de formulário no elemento root
ReactDOM.createRoot(document.getElementById('root')).render(<UserCreationForm />);