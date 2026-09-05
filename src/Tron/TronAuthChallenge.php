<?php

declare(strict_types=1);

namespace DeepCore\Tron;

use DateTimeImmutable;
use JsonException;
use RuntimeException;

final readonly class TronAuthChallenge
{
    public function __construct(
        public string $domain,
        public string $address,
        public string $nonce,
        public DateTimeImmutable $issuedAt,
        public DateTimeImmutable $expiresAt,
    ) {
        if ($domain === '') {
            throw new RuntimeException('AUTH_DOMAIN_REQUIRED');
        }
        if ($address === '') {
            throw new RuntimeException('AUTH_ADDRESS_REQUIRED');
        }
        if ($nonce === '') {
            throw new RuntimeException('AUTH_NONCE_REQUIRED');
        }
        if ($expiresAt <= $issuedAt) {
            throw new RuntimeException('AUTH_EXPIRATION_INVALID');
        }
    }

    /** @throws JsonException */
    public function canonicalMessage(): string
    {
        $payload = [
            'address' => $this->address,
            'domain' => $this->domain,
            'expires_at' => $this->expiresAt->format(DATE_ATOM),
            'issued_at' => $this->issuedAt->format(DATE_ATOM),
            'nonce' => $this->nonce,
            'version' => 1,
        ];

        ksort($payload);

        return json_encode(
            $payload,
            JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR
        );
    }
}
