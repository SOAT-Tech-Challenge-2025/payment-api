# API de Pagamentos

## Build de imagens

### Desenvolvimento / Teste
```sh
docker build --target development -t payment-api:dev .
```

### Produção
```sh
docker build --target production -t payment-api:latest .
```

## Testes
```sh
docker run --rm payment-api:dev pytest
```
