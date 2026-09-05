<?php

declare(strict_types=1);

use DeepCore\Tron\SqliteAtomicNonceStore;
use PHPUnit\Framework\TestCase;

final class TronAtomicNonceStoreTest extends TestCase
{
    private function store(): SqliteAtomicNonceStore
    {
        $pdo = new PDO('sqlite::memory:');
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        return new SqliteAtomicNonceStore($pdo);
    }

    public function testOnlyFirstConsumptionSucceeds(): void
    {
        $store = $this->store();
        $store->issue('n-1', 'TADDRESS1', 200);

        self::assertTrue($store->consume('n-1', 'TADDRESS1', 100));
        self::assertFalse($store->consume('n-1', 'TADDRESS1', 100));
    }

    public function testWrongAddressCannotConsumeNonce(): void
    {
        $store = $this->store();
        $store->issue('n-2', 'TADDRESS1', 200);

        self::assertFalse($store->consume('n-2', 'TATTACKER', 100));
        self::assertTrue($store->consume('n-2', 'TADDRESS1', 100));
    }

    public function testExpiredNonceCannotBeConsumed(): void
    {
        $store = $this->store();
        $store->issue('n-3', 'TADDRESS1', 200);

        self::assertFalse($store->consume('n-3', 'TADDRESS1', 200));
        self::assertFalse($store->consume('n-3', 'TADDRESS1', 201));
    }

    public function testUnknownNonceCannotBeConsumed(): void
    {
        $store = $this->store();

        self::assertFalse($store->consume('unknown', 'TADDRESS1', 100));
    }

    public function testConcurrentStyleDoubleConsumeHasExactlyOneWinner(): void
    {
        $pdo = new PDO('sqlite::memory:');
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $store = new SqliteAtomicNonceStore($pdo);
        $store->issue('n-concurrent', 'TADDRESS1', 500);

        $results = [
            $store->consume('n-concurrent', 'TADDRESS1', 100),
            $store->consume('n-concurrent', 'TADDRESS1', 100),
        ];

        self::assertSame(1, count(array_filter($results)));
        self::assertSame([true, false], $results);
    }
}
