<?php

declare(strict_types=1);

use DeepCore\Tron\TronAuthChallenge;
use DeepCore\Tron\TronAuthNonceStore;
use PHPUnit\Framework\TestCase;

final class TronMessageAuthTest extends TestCase
{
    private const ADDRESS = 'TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX';

    public function testNonceCanOnlyBeConsumedOnce(): void
    {
        $store = new TronAuthNonceStore();
        $now = 1_000;
        $store->issue('nonce-1', self::ADDRESS, $now + 300);

        self::assertTrue($store->consume('nonce-1', self::ADDRESS, $now));
        self::assertFalse($store->consume('nonce-1', self::ADDRESS, $now));
    }

    public function testExpiredNonceCannotBeConsumed(): void
    {
        $store = new TronAuthNonceStore();
        $store->issue('expired', self::ADDRESS, 1_010);

        self::assertFalse($store->consume('expired', self::ADDRESS, 1_010));
    }

    public function testWrongAddressCannotConsumeNonce(): void
    {
        $store = new TronAuthNonceStore();
        $store->issue('nonce-2', self::ADDRESS, 1_300);

        self::assertFalse($store->consume('nonce-2', 'TOTHERADDRESSXXXXXXXXXXXXXXXXXXXX', 1_000));
    }

    public function testUnknownNonceIsRejected(): void
    {
        $store = new TronAuthNonceStore();
        self::assertFalse($store->consume('unknown', self::ADDRESS, 1_000));
    }

    public function testCanonicalMessageIsDeterministic(): void
    {
        $issued = new DateTimeImmutable('2026-09-05T10:00:00+00:00');
        $expires = new DateTimeImmutable('2026-09-05T10:05:00+00:00');

        $challenge = new TronAuthChallenge(
            'auth.deepcore.local',
            self::ADDRESS,
            'nonce-canonical',
            $issued,
            $expires,
        );

        self::assertSame($challenge->canonicalMessage(), $challenge->canonicalMessage());
    }

    public function testDomainChangesCanonicalMessage(): void
    {
        $issued = new DateTimeImmutable('2026-09-05T10:00:00+00:00');
        $expires = new DateTimeImmutable('2026-09-05T10:05:00+00:00');

        $a = new TronAuthChallenge('auth.deepcore.local', self::ADDRESS, 'n', $issued, $expires);
        $b = new TronAuthChallenge('attacker.example', self::ADDRESS, 'n', $issued, $expires);

        self::assertNotSame($a->canonicalMessage(), $b->canonicalMessage());
    }

    public function testAddressChangesCanonicalMessage(): void
    {
        $issued = new DateTimeImmutable('2026-09-05T10:00:00+00:00');
        $expires = new DateTimeImmutable('2026-09-05T10:05:00+00:00');

        $a = new TronAuthChallenge('auth.deepcore.local', self::ADDRESS, 'n', $issued, $expires);
        $b = new TronAuthChallenge('auth.deepcore.local', 'TOTHERADDRESSXXXXXXXXXXXXXXXXXXXX', 'n', $issued, $expires);

        self::assertNotSame($a->canonicalMessage(), $b->canonicalMessage());
    }
}
